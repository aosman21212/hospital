from odoo import fields, models


class HospitalPatientTag(models.Model):
    _name        = 'hospital.patient.tag'
    _description = 'Patient Tag'
    _order       = 'name'

    name  = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Integer('Colour Index', default=0)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tag name must be unique.'),
    ]
