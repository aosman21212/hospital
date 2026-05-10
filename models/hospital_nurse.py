from odoo import api, fields, models, _


class HospitalNurse(models.Model):
    _name        = 'hospital.nurse'
    _description = 'Hospital Nurse'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'name'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name    = fields.Char('Full Name', required=True, tracking=True)
    ref     = fields.Char(
        'Nurse ID', copy=False, readonly=True,
        default=lambda self: _('New'), index=True,
    )
    photo   = fields.Image('Photo', max_width=1024, max_height=1024)
    user_id = fields.Many2one(
        'res.users', 'Linked Odoo User',
        ondelete='set null', index=True,
    )

    # ── Professional ──────────────────────────────────────────────────────

    specialisation = fields.Selection([
        ('general',     'General Nursing'),
        ('icu',         'ICU / Critical Care'),
        ('pediatric',   'Pediatric Nursing'),
        ('midwifery',   'Midwifery'),
        ('surgical',    'Surgical Nursing'),
        ('emergency',   'Emergency Nursing'),
        ('psychiatric', 'Psychiatric Nursing'),
        ('oncology',    'Oncology Nursing'),
        ('other',       'Other'),
    ], default='general', tracking=True)

    degree     = fields.Char('Degree / Qualifications')
    license_no = fields.Char('Nursing License No.')

    # ── Contact ───────────────────────────────────────────────────────────

    phone = fields.Char('Phone', tracking=True)
    email = fields.Char('Email')

    # ── Assignments ───────────────────────────────────────────────────────

    assignment_ids = fields.One2many(
        'hospital.nurse.assignment', 'nurse_id', string='Assignments',
    )
    assignment_count = fields.Integer(compute='_compute_assignment_count')
    current_ward_id  = fields.Many2one(
        'hospital.ward', string='Current Ward',
        compute='_compute_current_ward', store=False,
    )

    # ── Status ────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('active',   'Active'),
        ('on_leave', 'On Leave'),
        ('inactive', 'Inactive'),
    ], default='active', tracking=True, index=True)

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, index=True,
    )
    note = fields.Text('Notes')

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for rec in self:
            rec.assignment_count = len(rec.assignment_ids)

    @api.depends('assignment_ids', 'assignment_ids.state', 'assignment_ids.ward_id')
    def _compute_current_ward(self):
        for rec in self:
            active = rec.assignment_ids.filtered(lambda a: a.state == 'active')
            rec.current_ward_id = active[:1].ward_id if active else False

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', _('New')) == _('New'):
                vals['ref'] = (
                    self.env['ir.sequence'].next_by_code('hospital.nurse')
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

    def action_view_assignments(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Assignments — %s') % self.name,
            'res_model': 'hospital.nurse.assignment',
            'view_mode': 'list,form',
            'domain':    [('nurse_id', '=', self.id)],
            'context':   {'default_nurse_id': self.id},
        }
