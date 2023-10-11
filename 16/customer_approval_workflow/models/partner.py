# -*- coding: utf-8 -*-
import json
from lxml import etree
from odoo import models, api, fields
from odoo.addons.base.models.ir_ui_view import transfer_node_to_modifiers, transfer_modifiers_to_node
from odoo.tools import safe_eval


class PartnerView(models.Model):

    _inherit = 'res.partner'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], required=True, default='draft', tracking=True, string='Status', readonly=True)

    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        args += [('state', '=', 'approved')]
        res = super(PartnerView, self).name_search(
            name, args=args, operator=operator, limit=limit)
        return res

    def partner_approve(self):
        self.write({'state': 'approved'})
        self.approved_by = self.env.user.id

    def partner_set_draft(self):
        self.write({'state': 'draft'})

    def partner_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def get_view(self, view_id=None, view_type='form',  **options):
        res = super(PartnerView, self).get_view(view_id, view_type, **options)
        view_fields = res.get('models').get('res.partner')
        res['fields'] = self.fields_get(view_fields)
        if view_type == "form":
            doc = etree.XML(res['arch'])
            for node in doc.iter(tag="field"):
                if 'readonly' in node.attrib.get("modifiers", ''):
                    attrs = json.loads(node.attrib.get("modifiers", ''))
                    if 'readonly' in attrs:
                        attrs_dict = attrs
                        readonly_list = attrs_dict.get('readonly',)
                        if type(readonly_list) == list:
                            readonly_list.insert(0, ('state', '=', 'approved'))
                            if len(readonly_list) > 1:
                                readonly_list.insert(0, '|')
                        attrs_dict.update({'readonly': readonly_list})
                        node.set('attrs', str(attrs_dict))
                        transfer_node_to_modifiers(
                            node, attrs_dict)
                        transfer_modifiers_to_node(
                            attrs_dict, node)
                        continue
                    else:
                        continue
                attrs_dict = json.loads(node.attrib.get("modifiers", '')) if node.attrib.get("modifiers", '') else {}
                attrs_dict.update({'readonly': [('state', '=', 'approved')]})
                node.set('attrs', str(attrs_dict))
                transfer_node_to_modifiers(
                    node, attrs_dict)
                transfer_modifiers_to_node(
                    attrs_dict, node)
            res['arch'] = etree.tostring(doc)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PartnerView, self).create(vals_list)
        if not self.env.user.has_group('customer_approval_workflow.group_contact_manager'):
            ctx = {}
            email_list = [user.email for user in self.env['res.users'].sudo().search(
                []) if user.has_group('customer_approval_workflow.group_contact_manager')]
            if email_list:
                ctx['partner_manager_email'] = ','.join(
                    [email for email in email_list if email])
                ctx['email_from'] = self.env.user.email
                ctx['user_name'] = self.env.user.name
                ctx['company'] = self.env.user.company_id.name
                ctx['lang'] = self.env.user.lang
                template = self.env.ref(
                    'customer_approval_workflow.customer_approval_email_template_ip')
                ctx['db'] = self.env.cr.dbname
                template.with_context(ctx).sudo().send_mail(
                    res.id, force_send=True, raise_exception=False)
        return res
