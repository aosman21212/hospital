from odoo import fields, models


class HospitalLabResultImage(models.Model):
    """One image/scan per record linked to a lab test — allows unlimited results."""
    _name        = 'hospital.lab.result.image'
    _description = 'Lab Test Result Image'
    _order       = 'sequence, id'

    test_id   = fields.Many2one(
        'hospital.lab.test', 'Lab Test',
        required=True, ondelete='cascade', index=True,
    )
    sequence  = fields.Integer('Sequence', default=10)
    name      = fields.Char('Description', default='Result Image')
    image     = fields.Binary('Image / Scan', attachment=True, required=True)
    image_filename = fields.Char('Filename')
    image_thumb    = fields.Binary('Thumbnail', compute='_compute_thumb',
                                   store=True, attachment=True)
    note      = fields.Char('Note')

    def _compute_thumb(self):
        """Create a 256x256 thumbnail for gallery display."""
        for rec in self:
            if rec.image:
                try:
                    from odoo.tools.image import image_process
                    rec.image_thumb = image_process(
                        rec.image, size=(256, 256), crop='center',
                    )
                except Exception:
                    rec.image_thumb = rec.image
            else:
                rec.image_thumb = False
