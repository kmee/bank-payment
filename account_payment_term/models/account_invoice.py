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

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_terms = fields.One2many(
        string='Payment Term',
        comodel_name='account.invoice.term',
        inverse_name='invoice_term',
        readonly=True,
        states={'draft': [('readonly', False)]},
        # copy=False,
        ondelete='set null',
    )

    @api.onchange('payment_terms')
    def onchange_payment_terms(self):
        for invoice in self:
            for pts in invoice.payment_terms:
                pts._onchange_calc_amount()
                if pts.payment_term_id != invoice.payment_term:
                    pts.unlink()

    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        invoice_ids = self.ids

        res = super(AccountInvoice, self.with_context(
            invoice_ids=invoice_ids,
            payment_term_id=payment_term_id)
            ).onchange_payment_term_date_invoice(payment_term_id, date_invoice)

        pt = self.env['account.payment.term'].browse(payment_term_id)
        if pt:
            new_payments = pt.compute(1, date_invoice)[0]
            payments = pt.with_context(
                payment_term_id=pt.id,
                invoice_ids=invoice_ids).set_payments(new_payments)
            if pt.compare_payments(self.payment_terms, payments):
                res['value'].update({'payment_terms': payments})

        else:
            res['value'].update({'payment_terms': {}})

        return res


class AccountInvoiceTerm(models.Model):
    _name = 'account.invoice.term'
    _inherit = 'account.payment.term.model'
    _description = 'Invoice Payment Term'

    payment_term_id = fields.Many2one(comodel_name='account.payment.term')
    invoice_term = fields.Many2one(comodel_name='account.invoice')

    @api.onchange('percent', 'payment_date', 'invoice_term', 'payment_term_id')
    def _onchange_calc_amount(self):
        for line in self:
            if line.invoice_term:
                line.amount = line.invoice_term.amount_total*line.percent
