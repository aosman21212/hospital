from odoo import api, fields, models


class HospitalPrescriptionLine(models.Model):
    _name        = 'hospital.prescription.line'
    _description = 'Prescription Line'
    _order       = 'sequence, id'

    prescription_id = fields.Many2one(
        'hospital.prescription', 'Prescription',
        required=True, ondelete='cascade', index=True,
    )
    sequence   = fields.Integer('Sequence', default=10)

    # ── Medicine ──────────────────────────────────────────────────────────

    product_id = fields.Many2one(
        'product.product', 'Medicine / Drug',
        required=True, ondelete='restrict',
    )
    name       = fields.Char('Medicine Name', required=True)
    dosage     = fields.Char('Dosage', help='e.g. 500 mg, 10 ml, 1 tablet')

    # ── Administration ────────────────────────────────────────────────────

    route = fields.Selection([
        ('oral',        'Oral'),
        ('injection',   'Injection (IV/IM)'),
        ('topical',     'Topical'),
        ('inhalation',  'Inhalation'),
        ('sublingual',  'Sublingual'),
        ('rectal',      'Rectal'),
        ('ophthalmic',  'Ophthalmic (Eye)'),
        ('otic',        'Otic (Ear)'),
        ('nasal',       'Nasal'),
        ('other',       'Other'),
    ], default='oral')

    frequency = fields.Selection([
        ('once',          'Once Daily'),
        ('twice',         'Twice Daily (BD)'),
        ('three_times',   'Three Times Daily (TDS)'),
        ('four_times',    'Four Times Daily (QDS)'),
        ('every_8h',      'Every 8 Hours'),
        ('every_6h',      'Every 6 Hours'),
        ('at_bedtime',    'At Bedtime'),
        ('as_needed',     'As Needed (PRN)'),
        ('stat',          'Immediately (STAT)'),
    ], default='once')

    duration      = fields.Char('Duration', help='e.g. 5 days, 2 weeks')
    instructions  = fields.Char('Special Instructions',
                                 help='e.g. Take with food, Avoid sunlight')

    # ── Quantity & Price ──────────────────────────────────────────────────

    qty        = fields.Float('Qty', default=1.0)
    price_unit = fields.Float('Unit Price')
    subtotal   = fields.Float(
        'Subtotal', compute='_compute_subtotal', store=True, readonly=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name       = self.product_id.display_name
            self.price_unit = self.product_id.list_price
