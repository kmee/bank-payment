# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPaymentApiLineClose(models.TransientModel):
    _name = "account.payment.api.line.close"
    _description = "Close a Payment with Unknown Status after Checking at the Bank"

    _api_second_factor_methods = ("_api_close_confirmed",)

    name = fields.Char(related="line_id.order_id.name")
    line_id = fields.Many2one(
        comodel_name="account.payment.api.line", required=True, readonly=True
    )
    partner_id = fields.Many2one(related="line_id.partner_id")
    amount = fields.Monetary(related="line_id.amount")
    currency_id = fields.Many2one(related="line_id.currency_id")
    outcome = fields.Selection(
        selection=[("paid", "Paid"), ("refused", "Not Paid")],
        string="At the Bank",
        required=True,
    )
    reason = fields.Text(required=True)
    checked = fields.Boolean(string="I checked this payment at the bank")

    def _api_second_factor_orders(self):
        return self.line_id.order_id

    def _api_check_close(self):
        self.ensure_one()
        if not self.checked:
            raise UserError(_("Confirm that you checked this payment at the bank."))
        if not self.reason.strip():
            raise UserError(_("Give the reason for closing this payment."))
        self.line_id._api_check_can_close()

    def action_confirm(self):
        self._api_check_close()
        return self.env["account.payment.api.second.factor"]._run_after_check(
            self,
            "_api_close_confirmed",
            required=self.line_id.order_id.payment_mode_id.api_require_second_factor,
        )

    def _api_close_confirmed(self):
        self._api_check_close()
        self.line_id._api_close_unknown(self.outcome, self.reason.strip())
        return {"type": "ir.actions.client", "tag": "reload"}
