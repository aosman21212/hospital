from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalPrescription(models.Model):
    _name        = 'hospital.prescription'
    _description = 'Pharmacy Prescription'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'prescription_date desc, name desc'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name = fields.Char(
        'Prescription No.', copy=False, readonly=True,
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
        'res.users', 'Prescribing Doctor',
        required=True, tracking=True,
        default=lambda self: self.env.user,
        domain=[('share', '=', False)],
    )

    # ── Dates ─────────────────────────────────────────────────────────────

    prescription_date = fields.Date(
        'Date', default=fields.Date.today, required=True, tracking=True,
    )
    valid_until = fields.Date('Valid Until')

    # ── State ─────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('draft',      'Draft'),
        ('confirmed',  'Confirmed'),
        ('dispensed',  'Dispensed'),
        ('cancelled',  'Cancelled'),
    ], default='draft', tracking=True, index=True)

    # ── Lines ─────────────────────────────────────────────────────────────

    line_ids = fields.One2many(
        'hospital.prescription.line', 'prescription_id',
        string='Medicines',
    )

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )
    notes = fields.Text('Clinical Notes')
    pharmacist_note = fields.Text('Pharmacist Notes')

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hospital.prescription')
                    or _('New')
                )
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Cannot confirm a prescription with no medicines.'))
        self.write({'state': 'confirmed'})

    def action_dispense(self):
        self.write({'state': 'dispensed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
