from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalLabTest(models.Model):
    _name        = 'hospital.lab.test'
    _description = 'Lab Test'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'request_date desc, name desc'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name = fields.Char(
        'Test Reference', copy=False, readonly=True,
        default=lambda self: _('New'), index=True,
    )

    # ── Links ─────────────────────────────────────────────────────────────

    patient_id = fields.Many2one(
        'hospital.patient', 'Patient',
        required=True, ondelete='restrict',
        tracking=True, index=True,
    )
    appointment_id = fields.Many2one(
        'hospital.appointment', 'Appointment',
        ondelete='set null', index=True,
        domain="[('patient_id', '=', patient_id)]",
    )
    doctor_id = fields.Many2one(
        'res.users', 'Requesting Doctor',
        default=lambda self: self.env.user,
        domain=[('share', '=', False)], tracking=True,
    )
    lab_technician = fields.Char('Lab Technician')

    # ── Test Details ──────────────────────────────────────────────────────

    test_type_id = fields.Many2one(
        'hospital.lab.test.type', 'Test Type',
        required=True, ondelete='restrict', tracking=True,
    )
    category = fields.Selection(
        related='test_type_id.category', store=True, readonly=True,
    )
    request_date = fields.Datetime(
        'Requested On', default=fields.Datetime.now, tracking=True,
    )
    result_date  = fields.Datetime('Result Date', tracking=True)

    # ── State ─────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('requested',        'Requested'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress',      'In Progress'),
        ('completed',        'Completed'),
        ('cancelled',        'Cancelled'),
    ], default='requested', tracking=True, index=True)

    # ── Numeric Result ────────────────────────────────────────────────────

    result_value  = fields.Float('Result Value', digits=(12, 4))
    result_unit   = fields.Char('Unit', help='e.g. mg/dL, mmol/L, cells/μL')
    result_status = fields.Selection([
        ('normal',   'Normal'),
        ('high',     'High'),
        ('low',      'Low'),
        ('critical', 'Critical'),
    ], string='Status', tracking=True)
    normal_range  = fields.Text(
        related='test_type_id.normal_range', readonly=True, string='Normal Range',
    )

    # ── Text Result ───────────────────────────────────────────────────────

    result_text = fields.Text('Result / Findings',
                               help='Enter the lab findings, diagnoses or text results here.')

    # ── Image Results (primary + extra) ───────────────────────────────────

    result_image          = fields.Binary(
        'Primary Image', attachment=True,
        help='Upload the primary result image (X-Ray, Scan, Report photo).',
    )
    result_image_filename = fields.Char('Image Filename')
    result_image_ids      = fields.One2many(
        'hospital.lab.result.image', 'test_id',
        string='All Result Images',
        help='Add unlimited scans, X-rays or photos for this test.',
    )
    image_count           = fields.Integer(
        compute='_compute_image_count', string='Images',
    )

    # ── Company & Notes ───────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )
    note = fields.Text('Internal Notes')

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('result_image_ids')
    def _compute_image_count(self):
        for rec in self:
            cnt = len(rec.result_image_ids)
            if rec.result_image:
                cnt += 1
            rec.image_count = cnt

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hospital.lab.test')
                    or _('New')
                )
        return super().create(vals_list)

    # ── Onchange ──────────────────────────────────────────────────────────

    @api.onchange('test_type_id')
    def _onchange_test_type_id(self):
        if self.test_type_id:
            self.result_unit = ''

    # ── State transitions ─────────────────────────────────────────────────

    def action_collect_sample(self):
        self.write({'state': 'sample_collected'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        for rec in self:
            if not rec.result_text and not rec.result_image and not rec.result_image_ids:
                raise UserError(_(
                    'Please enter a result (text or image) before marking the test as completed.'
                ))
        self.write({
            'state': 'completed',
            'result_date': fields.Datetime.now(),
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'requested'})
