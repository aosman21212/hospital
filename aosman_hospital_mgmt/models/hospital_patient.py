from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalPatient(models.Model):
    _name        = 'hospital.patient'
    _description = 'Hospital Patient'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'name'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name      = fields.Char('Full Name', required=True, tracking=True)
    ref       = fields.Char(
        'Patient Reference', copy=False, readonly=True,
        default=lambda self: _('New'), index=True,
    )
    photo     = fields.Image('Photo', max_width=1024, max_height=1024)
    partner_id = fields.Many2one(
        'res.partner', 'Linked Contact',
        ondelete='set null', index=True,
        help='Link this patient to an existing Odoo contact for invoicing.',
    )

    # ── Medical Info ──────────────────────────────────────────────────────

    dob = fields.Date('Date of Birth', tracking=True)
    age = fields.Integer(
        'Age', compute='_compute_age', store=False,
        help='Calculated from Date of Birth.',
    )
    gender = fields.Selection([
        ('male',   'Male'),
        ('female', 'Female'),
        ('other',  'Other'),
    ], tracking=True)
    blood_group = fields.Selection([
        ('a+',  'A+'), ('a-',  'A−'),
        ('b+',  'B+'), ('b-',  'B−'),
        ('ab+', 'AB+'), ('ab-', 'AB−'),
        ('o+',  'O+'), ('o-',  'O−'),
    ], string='Blood Group', tracking=True)

    # ── Contact ───────────────────────────────────────────────────────────

    phone = fields.Char('Phone', tracking=True)
    email = fields.Char('Email')

    # ── Tags ──────────────────────────────────────────────────────────────

    tag_ids = fields.Many2many(
        'hospital.patient.tag',
        'hospital_patient_tag_rel', 'patient_id', 'tag_id',
        string='Tags',
    )

    # ── Appointments ──────────────────────────────────────────────────────

    appointment_ids = fields.One2many(
        'hospital.appointment', 'patient_id', string='Appointments',
    )
    appointment_count = fields.Integer(
        compute='_compute_appointment_count', string='Appts.',
    )

    # ── Lab Tests ─────────────────────────────────────────────────────────

    lab_test_ids = fields.One2many(
        'hospital.lab.test', 'patient_id', string='Lab Tests',
    )
    lab_test_count = fields.Integer(
        compute='_compute_lab_test_count', string='Lab Tests',
    )

    # ── Prescriptions ─────────────────────────────────────────────────────

    prescription_ids = fields.One2many(
        'hospital.prescription', 'patient_id', string='Prescriptions',
    )
    prescription_count = fields.Integer(
        compute='_compute_prescription_count', string='Prescriptions',
    )

    # ── Status ────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('draft',      'Draft'),
        ('active',     'Active'),
        ('discharged', 'Discharged'),
    ], default='draft', tracking=True, index=True)

    # ── Medical History ───────────────────────────────────────────────────

    allergies           = fields.Char('Allergies',
                                       help='e.g. Penicillin, Peanuts, Latex')
    chronic_conditions  = fields.Char('Chronic Conditions',
                                       help='e.g. Diabetes Type 2, Hypertension')
    current_medications = fields.Text('Current Medications')
    past_surgeries      = fields.Text('Past Surgeries / Procedures')
    family_history      = fields.Text('Family Medical History')
    medical_history     = fields.Html('Full Medical History')

    emergency_contact   = fields.Char('Emergency Contact Name')
    emergency_phone     = fields.Char('Emergency Contact Phone')
    emergency_relation  = fields.Selection([
        ('spouse',  'Spouse'),
        ('parent',  'Parent'),
        ('child',   'Child'),
        ('sibling', 'Sibling'),
        ('friend',  'Friend'),
        ('other',   'Other'),
    ], string='Relationship to Patient')

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company, index=True,
    )
    note = fields.Html('Internal Notes')

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('dob')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.dob:
                rec.age = (
                    today.year - rec.dob.year
                    - ((today.month, today.day) < (rec.dob.month, rec.dob.day))
                )
            else:
                rec.age = 0

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    @api.depends('lab_test_ids')
    def _compute_lab_test_count(self):
        for rec in self:
            rec.lab_test_count = len(rec.lab_test_ids)

    @api.depends('prescription_ids')
    def _compute_prescription_count(self):
        for rec in self:
            rec.prescription_count = len(rec.prescription_ids)

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', _('New')) == _('New'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or _('New')
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────────

    def action_activate(self):
        self.write({'state': 'active'})

    def action_discharge(self):
        self.write({'state': 'discharged'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Smart button ──────────────────────────────────────────────────────

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Appointments — %s') % self.name,
            'res_model': 'hospital.appointment',
            'view_mode': 'list,calendar,form',
            'domain':    [('patient_id', '=', self.id)],
            'context':   {'default_patient_id': self.id},
        }

    def action_view_lab_tests(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Lab Tests — %s') % self.name,
            'res_model': 'hospital.lab.test',
            'view_mode': 'list,form',
            'domain':    [('patient_id', '=', self.id)],
            'context':   {'default_patient_id': self.id},
        }

    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Prescriptions — %s') % self.name,
            'res_model': 'hospital.prescription',
            'view_mode': 'list,form',
            'domain':    [('patient_id', '=', self.id)],
            'context':   {'default_patient_id': self.id},
        }
