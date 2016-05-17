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

from openerp import fields, models
from openerp.addons import decimal_precision as dp


class AccountPaymentLineModel(models.AbstractModel):

    _name = 'account.payment.term.model'
    _description = 'Account Payment Term Model'

    date = fields.Date(
        string='Date',
    )
    amount = fields.Float(
        string='amount',
        digits=dp.get_precision('Account')
    )
