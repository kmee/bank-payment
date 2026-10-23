# Copyright 2016-2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentMode(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.res_users_model = cls.env["res.users"]
        cls.journal_model = cls.env["account.journal"]
        cls.payment_mode_model = cls.env["account.payment.mode"]

        # refs
        cls.manual_out = cls.env.ref("account.account_payment_method_manual_out")
        # Company
        cls.company = cls.env.ref("base.main_company")

        # Company 2
        cls.company_2 = cls.env["res.company"].create({"name": "Company 2"})

        cls.journal_c1 = cls._create_journal("J1", cls.company)
        cls.journal_c2 = cls._create_journal("J2", cls.company_2)
        cls.journal_c3 = cls._create_journal("J3", cls.company)

        cls.payment_mode_c1 = cls.payment_mode_model.create(
            {
                "name": "Direct Debit of suppliers from Bank 1",
                "bank_account_link": "variable",
                "payment_method_id": cls.manual_out.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal_c1.id,
                "variable_journal_ids": [
                    (6, 0, [cls.journal_c1.id, cls.journal_c3.id])
                ],
            }
        )

    @classmethod
    def _create_journal(cls, name, company):
        # Create a cash account
        # Create a journal for cash account
        journal = cls.journal_model.create(
            {"name": name, "code": name, "type": "bank", "company_id": company.id}
        )
        return journal

    def test_payment_mode_company_consistency_change(self):
        # Assertion on the constraints to ensure the consistency
        # for company dependent fields
        with self.assertRaises(UserError):
            self.payment_mode_c1.write({"fixed_journal_id": self.journal_c2.id})
        with self.assertRaises(UserError):
            self.payment_mode_c1.write(
                {
                    "variable_journal_ids": [
                        Command.set(
                            [
                                self.journal_c1.id,
                                self.journal_c2.id,
                                self.journal_c3.id,
                            ],
                        )
                    ]
                }
            )
        with self.assertRaises(ValidationError):
            self.journal_c1.write({"company_id": self.company_2.id})

    def test_payment_mode_company_consistency_create(self):
        # Assertion on the constraints to ensure the consistency
        # for company dependent fields
        with self.assertRaises(UserError):
            self.payment_mode_model.create(
                {
                    "name": "Direct Debit of suppliers from Bank 2",
                    "bank_account_link": "variable",
                    "payment_method_id": self.manual_out.id,
                    "company_id": self.company.id,
                    "fixed_journal_id": self.journal_c2.id,
                }
            )

        with self.assertRaises(UserError):
            self.payment_mode_model.create(
                {
                    "name": "Direct Debit of suppliers from Bank 3",
                    "bank_account_link": "variable",
                    "payment_method_id": self.manual_out.id,
                    "company_id": self.company.id,
                    "variable_journal_ids": [(6, 0, [self.journal_c2.id])],
                }
            )

        with self.assertRaises(UserError):
            self.payment_mode_model.create(
                {
                    "name": "Direct Debit of suppliers from Bank 4",
                    "bank_account_link": "fixed",
                    "payment_method_id": self.manual_out.id,
                    "company_id": self.company.id,
                }
            )
        self.journal_c1.outbound_payment_method_line_ids = False
        with self.assertRaises(ValidationError):
            self.payment_mode_model.create(
                {
                    "name": "Direct Debit of suppliers from Bank 5",
                    "bank_account_link": "fixed",
                    "payment_method_id": self.manual_out.id,
                    "company_id": self.company.id,
                    "fixed_journal_id": self.journal_c1.id,
                }
            )
        self.journal_c1.inbound_payment_method_line_ids = False
        with self.assertRaises(ValidationError):
            self.payment_mode_model.create(
                {
                    "name": "Direct Debit of suppliers from Bank 5",
                    "bank_account_link": "fixed",
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "company_id": self.company.id,
                    "fixed_journal_id": self.journal_c1.id,
                }
            )


@tagged("post_install", "-at_install")
class TestAccountPaymentMethodDisplayName(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.method_out = cls.env["account.payment.method"].create(
            {"name": "Test Method", "code": "TST", "payment_type": "outbound"}
        )
        cls.method_in = cls.env["account.payment.method"].create(
            {"name": "Test Method", "code": "TST", "payment_type": "inbound"}
        )

    def test_display_name_uses_selection_label(self):
        """The display name shows the selection label, not the technical value."""
        self.assertEqual(
            self.method_out.with_context(lang="en_US").display_name,
            "[TST] Test Method (Outbound)",
        )
        self.assertEqual(
            self.method_in.with_context(lang="en_US").display_name,
            "[TST] Test Method (Inbound)",
        )

    def test_display_name_is_translated(self):
        """The payment type label follows the language of the user."""
        lang = self.env["res.lang"]._activate_lang("pt_BR")
        self.env["base.language.install"].create(
            {"lang_ids": [Command.set(lang.ids)], "overwrite": True}
        ).lang_install()
        translated = dict(
            self.env["account.payment.method"]
            .with_context(lang="pt_BR")
            ._fields["payment_type"]
            ._description_selection(self.env(context={"lang": "pt_BR"}))
        )
        self.assertNotEqual(translated["outbound"], "Outbound")
        method = self.method_out.with_context(lang="pt_BR")
        self.assertEqual(
            method.display_name, f"[TST] Test Method ({translated['outbound']})"
        )
        self.assertNotIn("outbound", method.display_name)
