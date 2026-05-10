from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalNurseAssignment(models.Model):
    _name        = 'hospital.nurse.assignment'
    _description = 'Nurse Assignment'
    _inherit     = ['mail.thread']
    _order       = 'date_start desc, nurse_id'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name = fields.Char(
        'Reference', compute='_compute_name', store=True,
    )

    # ── Links ─────────────────────────────────────────────────────────────

    nurse_id  = fields.Many2one(
        'hospital.nurse', 'Nurse',
        required=True, ondelete='cascade', tracking=True, index=True,
    )
    ward_id   = fields.Many2one(
        'hospital.ward', 'Ward',
        required=True, ondelete='restrict', tracking=True, index=True,
    )
    patient_id = fields.Many2one(
        'hospital.patient', 'Patient (optional)',
        ondelete='set null', index=True,
        help='Leave empty for a general ward assignment.',
    )

    # ── Shift ─────────────────────────────────────────────────────────────

    shift = fields.Selection([
        ('morning',   'Morning  06:00 – 14:00'),
        ('afternoon', 'Afternoon  14:00 – 22:00'),
        ('night',     'Night  22:00 – 06:00'),
        ('full_day',  'Full Day'),
    ], required=True, default='morning', tracking=True)

    date_start = fields.Date(
        'Start Date', required=True, default=fields.Date.today, tracking=True,
    )
    date_end = fields.Date('End Date', tracking=True)

    # ── State ─────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('scheduled',  'Scheduled'),
        ('active',     'Active'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ], default='scheduled', tracking=True, index=True)

    # ── Notes ─────────────────────────────────────────────────────────────

    note = fields.Text('Notes')

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('nurse_id', 'ward_id', 'date_start', 'shift')
    def _compute_name(self):
        shift_labels = {
            'morning':   'Morning',
            'afternoon': 'Afternoon',
            'night':     'Night',
            'full_day':  'Full Day',
        }
        for rec in self:
            nurse = rec.nurse_id.name or ''
            ward  = rec.ward_id.name  or ''
            shift = shift_labels.get(rec.shift, '')
            date  = str(rec.date_start) if rec.date_start else ''
            rec.name = '%s — %s (%s) %s' % (nurse, ward, shift, date)

    # ── State transitions ─────────────────────────────────────────────────

    def action_activate(self):
        for rec in self:
            if rec.state != 'scheduled':
                raise UserError(_('Only scheduled assignments can be activated.'))
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'completed':
                raise UserError(_('Completed assignments cannot be cancelled.'))
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'scheduled'})
