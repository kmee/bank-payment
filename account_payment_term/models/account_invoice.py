# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Mode module for OpenERP
#    Copyright (C) 2016 KMEE INFORMATICA LTDA (https://www.kmee.com.br/)
#    @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_terms = fields.One2many(
        string='Payment Term',
        comodel_name='account.invoice.term',
        inverse_name='invoice_term',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=True,
        ondelete='set null',
    )

    @api.onchange('payment_terms')
    def onchange_payment_terms(self):
        for invoice in self:
            for pts in invoice.payment_terms:
                if invoice.payment_term.id != pts.payment_term_id.id:
                    pts.unlink()
            # invoice.check_payment_terms()

    # @api.depends('payment_terms.amount',
    #              'payment_terms.percent')
    # def check_payment_terms(self):
    #     if not self.payment_terms or not self.amount_total:
    #         return
    #     self.payment_terms.onchange_amount()
    #     self.payment_terms.onchange_percent()

    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        if not payment_term_id:
            return {'value': {'payment_terms': False}}

        if self.payment_terms and (payment_term_id in
                                   [term.payment_term_id.id
                                    for term in self.payment_terms]):
            return {'value': {'date_due': max(
                self.payment_terms.mapped('payment_date')),
                              'payment_terms': self.payment_terms}}

        ctx = dict(self._context)
        ctx['invoice_ids'] = self.ids
        ctx['payment_term_id'] = payment_term_id
        result = super(AccountInvoice, self.with_context(
            ctx)).onchange_payment_term_date_invoice(
                payment_term_id, date_invoice)
        new_payments = self.payment_term.browse(payment_term_id).compute(
            1, date_invoice)
        if new_payments:
            payments = self.payment_term.browse(
                payment_term_id).with_context(ctx).set_payments(
                    new_payments[0])
            result['value'].update({'payment_terms': payments})
        return result

    @api.multi
    def action_move_create(self):
        result = []
        for invoice in self:
            ctx = dict(invoice._context)
            ctx['invoice_ids'] = invoice.id
            ctx['payment_term_id'] = invoice.payment_term
            invoice = invoice.with_context(ctx)
            result.append(super(AccountInvoice, invoice).action_move_create())
        return result


class AccountInvoiceTerm(models.Model):
    _name = 'account.invoice.term'
    _inherit = 'account.payment.term.model'
    _description = 'Invoice Payment Term'

    payment_term_id = fields.Many2one(comodel_name='account.payment.term')
    invoice_term = fields.Many2one(comodel_name='account.invoice')

