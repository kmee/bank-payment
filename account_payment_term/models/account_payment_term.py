# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Mode module for OpenERP
#    Copyright (C) 2016 KMEE INFORMATICA LTDA (https://www.kmee.com.br/)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
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
from openerp.addons import decimal_precision as dp
from openerp.osv import osv
from openerp.exceptions import Warning as UserError



class AccountPaymentTerm(osv.osv):
    _inherit = 'account.payment.term'

    # def compare_payments(self, inv_payments, new_payments):
    #     res = False
    #     for x in inv_payments:
    #         pt = [y[2]['payment_term_id'] for y in new_payments]
    #         if x.payment_term_id.id in pt:
    #             res = True
    #     return res

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        inv_id = context.get('invoice_ids', False)
        if inv_id:
            invoice = self.pool.get('account.invoice').browse(
                cr, uid, inv_id, context=context)
            if invoice.payment_terms:
                return [(line.payment_date, line.amount)
                        for line in invoice.payment_terms]
            else:
                res = super(AccountPaymentTerm, self).compute(cr, uid, id,
                                                              value, date_ref,
                                                              context=context)
                invoice.payment_terms = self.set_payments(cr, uid,
                                                          res, context=context)
                return [(line.payment_date, line.amount)
                        for line in invoice.payment_terms]

        return super(AccountPaymentTerm, self).compute(cr, uid, id,
                                                       value, date_ref,
                                                       context=context)

    def set_payments(self, cr, uid, values, context=None):
        inv_obj = self.pool.get('account.invoice')
        pt = context.get('payment_term_id', False)
        invoice_ids = context.get('invoice_ids', False)

        invoice = inv_obj.browse(cr, uid, invoice_ids, context=context)

        payments_list = [
            (0, False,
             {
                 'payment_date': payment[0],
                 'percent': payment[1],
                 'amount': invoice and invoice.amount_total*payment[1]or 0.0,
                 'invoice_term': invoice and invoice.id or False,
                 'payment_term_id': pt
             })
            for payment in values]
        return payments_list


class AccountPaymentLineModel(models.AbstractModel):

    _name = 'account.payment.term.model'
    _description = 'Account Payment Term Model'

    payment_date = fields.Date(string='Payment Date')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))
    percent = fields.Float(string="Porcentagem do Total")

    @api.onchange('amount')
    def onchange_amount(self):
        for line in self:
            if line.invoice_term:
                total_amount = line.invoice_term.amount_total
                percent = line.amount/total_amount
                line.percent = percent

    @api.onchange('percent')
    def onchange_percent(self):
        for line in self:
            if line.invoice_term:
                total_amount = line.invoice_term.amount_total
                amount = (total_amount*line.percent)
                line.amount = amount

    @api.depends('amount', 'percent')
    def check_totals(self):
        amount = 0.0
        percent = 0.0
        for line in self.invoice_term.payment_terms:
            amount += line.amount
            percent += line.percent
        if amount != 0.0 and amount != self.invoice_term.amount_total:
            raise UserError(_('Valor total das parcelas '
                              'diferente do total da fatura'))
        if percent != 0.0 and percent != 1.0:
            raise UserError(_('Porcentagem total das parcelas '
                              'diferente de 100%'))
