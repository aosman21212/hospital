from odoo import api, fields, models


class HospitalWard(models.Model):
    _name        = 'hospital.ward'
    _description = 'Hospital Ward'
    _order       = 'name'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name      = fields.Char('Ward Name', required=True)
    code      = fields.Char('Ward Code')
    ward_type = fields.Selection([
        ('general',     'General'),
        ('icu',         'ICU / Critical Care'),
        ('surgery',     'Surgery'),
        ('maternity',   'Maternity'),
        ('pediatric',   'Pediatric'),
        ('emergency',   'Emergency'),
        ('oncology',    'Oncology'),
        ('cardiac',     'Cardiac Care'),
        ('orthopedic',  'Orthopedic'),
        ('outpatient',  'Outpatient / OPD'),
    ], default='general', string='Type')

    # ── Physical ──────────────────────────────────────────────────────────

    bed_count   = fields.Integer('Total Beds', default=10)
    floor       = fields.Char('Floor / Building')
    description = fields.Text('Description')
    active      = fields.Boolean(default=True)

    # ── Relations ─────────────────────────────────────────────────────────

    nurse_assignment_ids = fields.One2many(
        'hospital.nurse.assignment', 'ward_id', string='Nurse Assignments',
    )
    nurse_count = fields.Integer(compute='_compute_nurse_count', string='Nurses on Duty')

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('nurse_assignment_ids', 'nurse_assignment_ids.state')
    def _compute_nurse_count(self):
        for rec in self:
            rec.nurse_count = len(
                rec.nurse_assignment_ids.filtered(lambda a: a.state == 'active')
            )
