from odoo import api, fields, models, _


class HospitalDoctor(models.Model):
    _name        = 'hospital.doctor'
    _description = 'Hospital Doctor'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'name'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name = fields.Char('Full Name', required=True, tracking=True)
    ref  = fields.Char(
        'Doctor ID', copy=False, readonly=True,
        default=lambda self: _('New'), index=True,
    )
    photo   = fields.Image('Photo', max_width=1024, max_height=1024)
    user_id = fields.Many2one(
        'res.users', 'Linked Odoo User',
        ondelete='set null', index=True,
        help='Link this doctor to an Odoo login account.',
    )

    # ── Professional ──────────────────────────────────────────────────────

    specialisation = fields.Selection([
        ('general',       'General Practice'),
        ('cardiology',    'Cardiology'),
        ('neurology',     'Neurology'),
        ('orthopedics',   'Orthopedics'),
        ('pediatrics',    'Pediatrics'),
        ('gynecology',    'Gynecology & Obstetrics'),
        ('dermatology',   'Dermatology'),
        ('ophthalmology', 'Ophthalmology'),
        ('ent',           'ENT (Ear, Nose & Throat)'),
        ('radiology',     'Radiology'),
        ('pathology',     'Pathology'),
        ('surgery',       'General Surgery'),
        ('psychiatry',    'Psychiatry'),
        ('oncology',      'Oncology'),
        ('urology',       'Urology'),
        ('other',         'Other'),
    ], string='Specialisation', tracking=True)

    degree = fields.Char('Degree / Qualifications',
                         help='e.g. MBBS, MD, FRCS')
    license_no = fields.Char('Medical License No.')

    # ── Contact ───────────────────────────────────────────────────────────

    phone = fields.Char('Phone', tracking=True)
    email = fields.Char('Email')

    # ── Schedule ──────────────────────────────────────────────────────────

    available_mon = fields.Boolean('Monday',    default=True)
    available_tue = fields.Boolean('Tuesday',   default=True)
    available_wed = fields.Boolean('Wednesday', default=True)
    available_thu = fields.Boolean('Thursday',  default=True)
    available_fri = fields.Boolean('Friday',    default=True)
    available_sat = fields.Boolean('Saturday',  default=False)
    available_sun = fields.Boolean('Sunday',    default=False)

    consultation_from     = fields.Float('Consulting Hours From', default=9.0,
                                          help='e.g. 9.0 = 09:00')
    consultation_to       = fields.Float('Consulting Hours To',   default=17.0)
    consultation_duration = fields.Integer('Slot Duration (min)', default=30)

    # ── Relations ─────────────────────────────────────────────────────────

    appointment_ids = fields.One2many(
        'hospital.appointment', 'doctor_profile_id', string='Appointments',
    )
    appointment_count = fields.Integer(compute='_compute_appointment_count')

    # ── Status ────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('active',    'Active'),
        ('on_leave',  'On Leave'),
        ('inactive',  'Inactive'),
    ], default='active', tracking=True, index=True)

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )
    note = fields.Text('Notes')

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', _('New')) == _('New'):
                vals['ref'] = (
                    self.env['ir.sequence'].next_by_code('hospital.doctor')
                    or _('New')
                )
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────────

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_set_on_leave(self):
        self.write({'state': 'on_leave'})

    def action_set_inactive(self):
        self.write({'state': 'inactive'})

    # ── Smart button ──────────────────────────────────────────────────────

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Appointments — Dr. %s') % self.name,
            'res_model': 'hospital.appointment',
            'view_mode': 'list,calendar,form',
            'domain':    [('doctor_profile_id', '=', self.id)],
            'context':   {'default_doctor_profile_id': self.id},
        }

    # ── Display helper ────────────────────────────────────────────────────

    def _get_schedule_summary(self):
        """Return a human-readable schedule string."""
        days = []
        mapping = [
            ('available_mon', 'Mon'), ('available_tue', 'Tue'),
            ('available_wed', 'Wed'), ('available_thu', 'Thu'),
            ('available_fri', 'Fri'), ('available_sat', 'Sat'),
            ('available_sun', 'Sun'),
        ]
        for field, label in mapping:
            if self[field]:
                days.append(label)
        h_from = '%02d:%02d' % (int(self.consultation_from),
                                 int((self.consultation_from % 1) * 60))
        h_to   = '%02d:%02d' % (int(self.consultation_to),
                                 int((self.consultation_to % 1) * 60))
        return '%s  |  %s – %s' % (', '.join(days) or 'No days set', h_from, h_to)
