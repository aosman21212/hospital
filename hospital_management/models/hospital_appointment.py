from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalAppointment(models.Model):
    _name        = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _inherit     = ['mail.thread', 'mail.activity.mixin']
    _order       = 'appointment_date desc, name desc'
    _rec_name    = 'name'

    # ── Identity ──────────────────────────────────────────────────────────

    name = fields.Char(
        'Reference', copy=False, readonly=True,
        default=lambda self: _('New'), index=True,
    )

    # ── Parties ───────────────────────────────────────────────────────────

    patient_id = fields.Many2one(
        'hospital.patient', 'Patient',
        required=True, ondelete='restrict',
        tracking=True, index=True,
    )
    doctor_id = fields.Many2one(
        'res.users', 'Assigned User / Doctor',
        required=True, tracking=True,
        default=lambda self: self.env.user,
        domain=[('share', '=', False)],
    )
    doctor_profile_id = fields.Many2one(
        'hospital.doctor', 'Doctor Profile',
        ondelete='set null', tracking=True, index=True,
    )

    # ── Scheduling ────────────────────────────────────────────────────────

    appointment_date = fields.Datetime(
        'Appointment Date & Time',
        required=True, tracking=True,
        default=fields.Datetime.now,
    )

    # ── State ─────────────────────────────────────────────────────────────

    state = fields.Selection([
        ('draft',       'Draft'),
        ('confirmed',   'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done',        'Done'),
        ('cancelled',   'Cancelled'),
    ], default='draft', tracking=True, index=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], default='0', string='Priority')

    # ── Lines ─────────────────────────────────────────────────────────────

    line_ids = fields.One2many(
        'hospital.appointment.line', 'appointment_id',
        string='Services / Medicines',
    )

    # ── Financials ────────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id,
    )
    amount_total = fields.Monetary(
        'Total Amount',
        compute='_compute_amount_total', store=True,
        currency_field='currency_id',
    )

    # ── Invoice link ──────────────────────────────────────────────────────

    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        copy=False, readonly=True, tracking=True,
        ondelete='set null',
    )
    invoice_payment_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment Status',
        store=True, readonly=True,
    )
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    # ── Lab Tests & Prescriptions ─────────────────────────────────────────

    lab_test_ids = fields.One2many(
        'hospital.lab.test', 'appointment_id', string='Lab Tests',
    )
    lab_test_count = fields.Integer(compute='_compute_lab_test_count')

    prescription_ids = fields.One2many(
        'hospital.prescription', 'appointment_id', string='Prescriptions',
    )
    prescription_count = fields.Integer(compute='_compute_prescription_count')

    # ── Admin ─────────────────────────────────────────────────────────────

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company, index=True,
    )
    notes = fields.Text('Notes')

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = 1 if rec.invoice_id else 0

    def _compute_lab_test_count(self):
        for rec in self:
            rec.lab_test_count = len(rec.lab_test_ids)

    def _compute_prescription_count(self):
        for rec in self:
            rec.prescription_count = len(rec.prescription_ids)

    # ── CRUD ──────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hospital.appointment')
                    or _('New')
                )
        return super().create(vals_list)

    # ── Onchange ──────────────────────────────────────────────────────────

    @api.onchange('doctor_profile_id')
    def _onchange_doctor_profile(self):
        if self.doctor_profile_id and self.doctor_profile_id.user_id:
            self.doctor_id = self.doctor_profile_id.user_id

    # ── State transitions ─────────────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft appointments can be confirmed.'))
        self.write({'state': 'confirmed'})
        # Schedule a reminder activity 24 h before the appointment
        self._schedule_reminder_activity()

    def action_start(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Only confirmed appointments can be started.'))
        self.write({'state': 'in_progress'})

    def action_done(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_('Only in-progress appointments can be marked done.'))
        self.write({'state': 'done'})

    def action_cancel(self):
        for rec in self:
            if rec.invoice_id and rec.invoice_id.state == 'posted':
                raise UserError(_(
                    'Cannot cancel appointment "%s": it has a posted invoice.\n'
                    'Please reset the invoice to draft or reverse it first.'
                ) % rec.name)
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Invoice creation ──────────────────────────────────────────────────

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return self.action_view_invoice()

        if self.state != 'done':
            raise UserError(_(
                'Please mark the appointment as Done before creating an invoice.'
            ))

        if not self.line_ids:
            raise UserError(_(
                'Cannot create an invoice: the appointment has no service lines.'
            ))

        # Resolve partner — patient's linked contact, or create one
        partner = self.patient_id.partner_id
        if not partner:
            raise UserError(_(
                'Patient "%s" has no linked Contact.\n'
                'Please set a Related Contact on the patient record before invoicing.'
            ) % self.patient_id.name)

        # Build invoice lines
        invoice_line_vals = []
        for line in self.line_ids:
            # Resolve income account
            account = line.account_id
            if not account:
                account = (
                    line.product_id.property_account_income_id
                    or line.product_id.categ_id.property_account_income_categ_id
                )
            if not account:
                raise UserError(_(
                    'Cannot create invoice: product "%s" has no income account configured.'
                ) % line.product_id.display_name)

            invoice_line_vals.append((0, 0, {
                'product_id':   line.product_id.id,
                'name':         line.name,
                'quantity':     line.qty,
                'price_unit':   line.price_unit,
                'account_id':   account.id,
            }))

        invoice = self.env['account.move'].create({
            'move_type':       'out_invoice',
            'partner_id':      partner.id,
            'company_id':      self.company_id.id,
            'currency_id':     self.currency_id.id,
            'invoice_origin':  self.name,
            'invoice_line_ids': invoice_line_vals,
        })

        self.invoice_id = invoice

        self.message_post(
            body=_(
                'Invoice <a href="#" data-oe-model="account.move" data-oe-id="%s">%s</a> created.'
            ) % (invoice.id, invoice.name),
        )
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('No invoice linked to this appointment.'))
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Invoice'),
            'res_model': 'account.move',
            'res_id':    self.invoice_id.id,
            'view_mode': 'form',
            'target':    'current',
        }

    def action_view_lab_tests(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Lab Tests — %s') % self.name,
            'res_model': 'hospital.lab.test',
            'view_mode': 'list,form',
            'domain':    [('appointment_id', '=', self.id)],
            'context':   {
                'default_patient_id':    self.patient_id.id,
                'default_appointment_id': self.id,
                'default_doctor_id':     self.doctor_id.id,
            },
        }

    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      _('Prescriptions — %s') % self.name,
            'res_model': 'hospital.prescription',
            'view_mode': 'list,form',
            'domain':    [('appointment_id', '=', self.id)],
            'context':   {
                'default_patient_id':    self.patient_id.id,
                'default_appointment_id': self.id,
                'default_doctor_id':     self.doctor_id.id,
            },
        }

    # ── Automated reminder ────────────────────────────────────────────────

    def _schedule_reminder_activity(self):
        """Schedule a reminder activity 24 h before the appointment date."""
        from datetime import timedelta
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return
        for rec in self:
            if not rec.appointment_date:
                continue
            remind_date = (rec.appointment_date - timedelta(hours=24)).date()
            # Remove any existing reminder for this appointment
            rec.activity_ids.filtered(
                lambda a: a.activity_type_id == activity_type
                and 'reminder' in (a.summary or '').lower()
            ).unlink()
            rec.activity_schedule(
                activity_type_id=activity_type.id,
                date_deadline=remind_date,
                summary=_('Appointment Reminder: %s') % rec.name,
                note=_('Reminder: appointment with %s on %s') % (
                    rec.patient_id.name,
                    rec.appointment_date.strftime('%d %b %Y %H:%M'),
                ),
                user_id=rec.doctor_id.id,
            )
