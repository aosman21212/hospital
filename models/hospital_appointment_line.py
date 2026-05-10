from odoo import api, fields, models


class HospitalAppointmentLine(models.Model):
    _name        = 'hospital.appointment.line'
    _description = 'Appointment Line'
    _order       = 'sequence, id'

    appointment_id = fields.Many2one(
        'hospital.appointment', 'Appointment',
        required=True, ondelete='cascade', index=True,
    )
    sequence   = fields.Integer('Sequence', default=10)
    product_id = fields.Many2one(
        'product.product', 'Product / Service',
        required=True, ondelete='restrict',
        domain=[('type', 'in', ['consu', 'service'])],
    )
    name       = fields.Char('Description', required=True)
    qty        = fields.Float('Qty', default=1.0, digits='Product Unit of Measure')
    price_unit = fields.Float('Unit Price', digits='Product Price')
    account_id = fields.Many2one(
        'account.account', 'Account',
        domain=[('deprecated', '=', False)],
        help='Override the default income account for this line.',
    )
    subtotal   = fields.Float(
        'Subtotal', compute='_compute_subtotal',
        store=True, digits='Product Price', readonly=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit

    # ── Onchange ──────────────────────────────────────────────────────────

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name       = self.product_id.display_name
            self.price_unit = self.product_id.list_price
            # Default account from product income account
            if self.product_id.property_account_income_id:
                self.account_id = self.product_id.property_account_income_id
            elif self.product_id.categ_id.property_account_income_categ_id:
                self.account_id = self.product_id.categ_id.property_account_income_categ_id
