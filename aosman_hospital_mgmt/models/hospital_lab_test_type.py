from odoo import fields, models


class HospitalLabTestType(models.Model):
    _name        = 'hospital.lab.test.type'
    _description = 'Lab Test Type'
    _order       = 'category, name'

    name     = fields.Char('Test Name', required=True, translate=True)
    code     = fields.Char('Code', help='Short code, e.g. CBC, XRAY, MRI')
    category = fields.Selection([
        ('blood',         'Blood / Haematology'),
        ('urine',         'Urine / Urinalysis'),
        ('imaging',       'Imaging (X-Ray, MRI, CT)'),
        ('microbiology',  'Microbiology / Culture'),
        ('biochemistry',  'Biochemistry'),
        ('other',         'Other'),
    ], required=True, default='blood')
    normal_range   = fields.Text('Normal Reference Range',
                                  help='Describe expected normal values for this test.')
    sample_type    = fields.Char('Sample Type',
                                  help='e.g. Venous Blood, Urine, Swab, Tissue')
    preparation    = fields.Text('Patient Preparation',
                                  help='Instructions before the test (fasting, etc.)')
    color          = fields.Integer('Colour Index', default=0)
    active         = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Lab test code must be unique.'),
    ]
