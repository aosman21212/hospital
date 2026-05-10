{
    'name': 'Hospital Management System',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Manage patients, appointments, billing and hospital operations',
    'description': """
Hospital Management System
==========================
A complete hospital management solution for Odoo 19.

Key Features
------------
- **Patient Management** — Create and manage patient records with photos,
  blood group, date of birth, contact info and custom tags.
- **Appointment Scheduling** — Full appointment lifecycle: Draft → Confirmed →
  In Progress → Done. Calendar view for daily/weekly scheduling.
- **Services & Medicines** — Appointment lines linked to Odoo products with
  qty, unit price and automatic subtotal computation.
- **Accounting Integration** — Generate vendor invoices directly from
  completed appointments with one click.
- **Patient Tagging** — Colour-coded tags (Urgent, Diabetic, Elderly, etc.)
  for quick patient categorisation and filtering.
- **Access Control** — Three security groups (Read Only / User / Manager)
  with company-based record rules for multi-company setups.
- **Smart Sequences** — Auto-generated references (HP/2026/0001 for patients,
  HA/2026/0001 for appointments).
- **PDF Reports** — Printable appointment sheet and patient card.
- **Mail & Activities** — Built-in chatter, followers and activity scheduling
  on patients and appointments.
    """,
    'author': 'abdzoro89',
    'website': 'https://apps.odoo.com',
    'depends': ['base', 'mail', 'account', 'product'],
    'data': [
        'security/res_groups.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/hospital_patient_tag_views.xml',
        'views/hospital_patient_views.xml',
        'views/hospital_appointment_views.xml',
        'views/hospital_doctor_views.xml',
        'views/hospital_nurse_views.xml',
        'views/hospital_lab_test_views.xml',
        'views/hospital_prescription_views.xml',
        'views/hospital_analytics_views.xml',
        'report/report_actions.xml',
        'report/report_appointment_template.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'images': ['static/description/banner.svg'],
    'post_init_hook': '_refresh_menu_icon',
}
