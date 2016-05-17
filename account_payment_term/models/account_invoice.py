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

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_terms = fields.One2many(
        string='Payment Term',
        relation='account.invoice.term',
        compute='_compute_payment_terms',
        # inverse='_set_payment_terms',
        # comodel_name='account.invoice.term',
        # inverse_name='invoice_term',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )

    @api.depends('payment_term', 'move_lines', 'date_due')
    def _compute_payment_terms(self):
        if self.move_lines:
            for line in self.move_lines:
                term = {
                    # 'date' :
                }
            # Computar a partir das move lins
            pass
        elif self.payment_term:
            # Computar a partir do modo de pagamento
            pass
        elif self.date_due:
            # Computar a partir da data de vencimento
            pass



    # # @api.multi
    # # @api.depends('payment_term', 'amount_total')
    # # def _compute_payment_term(self):
    # #     for record in self:
    # #         res = record.payment_term.compute(record.amount_total)
    # #         pass
    #
    # @api.multi
    # def onchange_payment_term_date_invoice(
    #         self, payment_term_id, date_invoice):
    #     ctx = dict(self.env.context)
    #     payment_terms = ctx.get('payment_terms', False)
    #
    #     if not payment_terms and not payment_term_id:
    #         res = super(
    #             AccountInvoice, self).onchange_payment_term_date_invoice(
    #             payment_term_id, date_invoice
    #         )
    #         vals = {'date': res['value']['date_due']}
    #         self.payment_terms.create(vals)
    #         return res
    #     res = []
    #     for item in payment_terms:
    #         res.append((item.date, item.amount))
    #     return res


class AccountInvoiceTerm(models.Model):
    _name = 'account.invoice.term'
    _inherit = 'account.payment.term.model'
    _description = 'Invoice Payment Term'

    # invoice_term = fields.Many2one(
    #     comodel_name='account.invoice',
    #     required=True,
    #     ondelete="cascade")
