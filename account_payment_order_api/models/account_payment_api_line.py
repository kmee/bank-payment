# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError

LINE_STATES = [
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("awaiting_release", "Awaiting Release at the Bank"),
    ("scheduled", "Scheduled"),
    ("processing", "Processing"),
    ("paid", "Paid"),
    ("refused", "Refused"),
    ("rejected", "Rejected"),
    ("cancelled", "Cancelled"),
    ("returned", "Returned"),
    ("unknown", "Unknown"),
]
# The journal item of a line in one of these states can be paid again.
RELEASED_STATES = ("refused", "rejected", "cancelled", "returned")
FINAL_STATES = ("paid",) + RELEASED_STATES
CANCELLABLE_STATES = ("accepted", "awaiting_release", "scheduled")


class AccountPaymentApiLine(models.Model):
    _name = "account.payment.api.line"
    _description = "Payment Line Sent to a Bank API"
    _order = "batch_id, id"

    batch_id = fields.Many2one(
        comodel_name="account.payment.api.batch",
        required=True,
        ondelete="cascade",
        index=True,
    )
    order_id = fields.Many2one(related="batch_id.order_id", store=True, index=True)
    company_id = fields.Many2one(related="batch_id.company_id", store=True)
    payment_line_id = fields.Many2one(
        comodel_name="account.payment.line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    move_line_id = fields.Many2one(related="payment_line_id.move_line_id", store=True)
    partner_id = fields.Many2one(related="payment_line_id.partner_id")
    amount = fields.Monetary(related="payment_line_id.amount_currency")
    currency_id = fields.Many2one(related="payment_line_id.currency_id")
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        compute="_compute_payment_id",
        help="Draft payment created when the order was confirmed; it is only "
        "posted when the bank reports the line as paid.",
    )
    state = fields.Selection(selection=LINE_STATES, default="pending", required=True)
    bank_reference = fields.Char(copy=False, help="Identifier of the line at the bank")
    reason = fields.Char(help="Reason given by the bank for the current status")
    authentication = fields.Char(help="Authentication code given by the bank")
    date_paid = fields.Date(readonly=True)
    amount_paid = fields.Monetary(readonly=True)

    def _compute_payment_id(self):
        for line in self:
            line.payment_id = line.payment_line_id.payment_ids[:1]

    def action_api_cancel(self):
        """Ask the bank to cancel lines it has not executed yet."""
        self.order_id._api_check_user_can_act()
        lines = self.filtered(lambda x: x.state in CANCELLABLE_STATES)
        if not lines:
            raise UserError(
                _("Only lines the bank has not executed yet can be cancelled.")
            )
        for batch in lines.batch_id:
            batch._api_cancel_lines(lines.filtered(lambda x, b=batch: x.batch_id == b))
        return True

    def _api_check_can_close(self):
        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(
                _("Only accounting managers close a payment checked at the bank.")
            )
        for line in self:
            if line.state != "unknown" or line.bank_reference:
                raise UserError(
                    _(
                        "Only a payment with unknown status and no identifier at the "
                        "bank can be closed by hand: use Check Bank Now for the others."
                    )
                )

    def action_api_close_unknown(self):
        self.ensure_one()
        self._api_check_can_close()
        return {
            "type": "ir.actions.act_window",
            "name": _("Close Payment Checked at the Bank"),
            "res_model": "account.payment.api.line.close",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
            "context": {"default_line_id": self.id},
        }

    def _api_close_unknown(self, outcome, reason):
        """Apply what the user found at the bank, as a check at the bank would."""
        self.ensure_one()
        self._api_check_can_close()
        self._api_apply({"state": outcome, "reason": reason})
        self.order_id._api_update_state()
        self.order_id.message_post(
            body=_(
                "%(user)s checked at the bank and closed the payment to %(partner)s "
                "as %(outcome)s: %(reason)s",
                user=self.env.user.name,
                partner=self.partner_id.name,
                outcome=_("paid") if outcome == "paid" else _("not paid"),
                reason=reason,
            ),
            author_id=self.env.user.partner_id.id,
            subtype_xmlid="mail.mt_note",
        )

    def _api_apply(self, result):
        """Apply a normalized provider result to the line.

        ``result`` keys: state (one of LINE_STATES), and optionally
        bank_reference, reason, authentication, date, amount.
        """
        self.ensure_one()
        new_state = result.get("state") or self.state
        if new_state not in dict(LINE_STATES):
            raise UserError(_("Unknown payment status %s from the bank.", new_state))
        if self.state in FINAL_STATES and self.state != "paid":
            return False
        if self.state == "paid" and new_state not in ("paid", "returned"):
            return False
        vals = {
            key: result[key]
            for key in ("bank_reference", "reason", "authentication")
            if result.get(key)
        }
        if new_state == "paid" and self.state != "paid":
            vals["date_paid"] = result.get("date") or fields.Date.context_today(self)
            vals["amount_paid"] = result.get("amount") or self.amount
            self._api_post_payment(vals["date_paid"])
        elif new_state in RELEASED_STATES and self.state != new_state:
            self._api_release_payment()
        vals["state"] = new_state
        self.sudo().write(vals)
        return True

    def _api_post_payment(self, date):
        payment = self.payment_id
        if not payment or payment.state in ("in_process", "paid"):
            return
        payment.date = date
        payment.action_post()
        (
            self.move_line_id
            + payment.move_id.line_ids.filtered(
                lambda x: x.account_id == payment.destination_account_id
            )
        ).reconcile()

    def _api_release_payment(self):
        for payment in self.payment_id.filtered(lambda p: p.state != "canceled"):
            if payment.move_id.state == "posted":
                payment.action_draft()
            payment.action_cancel()
