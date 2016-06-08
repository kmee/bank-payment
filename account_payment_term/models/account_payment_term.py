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


class AccountPaymentTerm(osv.osv):
    _inherit = 'account.payment.term'

    def compare_payments(self, inv_payments, new_payments):
        res = False
        for x in inv_payments:
            pt = [y[2]['payment_term_id'] for y in new_payments]
            if x.payment_term_id.id in pt:
                res = True
        return res

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        res = super(AccountPaymentTerm, self).compute(cr, uid, id,
                                                      value, date_ref,
                                                      context=context)
        invoice_ids = context.get('invoice_ids', False)

        if invoice_ids:
            inv_pts = self.pool.get('account.invoice').browse(cr, uid,
                                                              invoice_ids,
                                                              context=context)
            payments = self.set_payments(cr, uid, res, context=context)

            if (inv_pts.payment_terms and not
                    self.compare_payments(inv_pts.payment_terms, payments)):
                pts = inv_pts.payment_terms
                res = [(pt.payment_date, pt.amount) for pt in pts]
        else:
            pass
        return res

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
