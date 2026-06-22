from odoo.tests import common


class TestExampleModel(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.Example = self.env['my_custom_module.example']

    def test_create_record(self):
        record = self.Example.create({
            'name': 'Test Record',
        })
        self.assertEqual(record.name, 'Test Record')
        self.assertEqual(record.state, 'draft')
        self.assertTrue(record.active)

    def test_default_company(self):
        record = self.Example.create({
            'name': 'Test Company',
        })
        self.assertEqual(record.company_id, self.env.company)

    def test_active_default_true(self):
        record = self.Example.create({
            'name': 'Active Test',
        })
        self.assertTrue(record.active)
