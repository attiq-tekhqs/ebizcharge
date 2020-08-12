# -*- coding: utf-8 -*-

import pprint
import logging
from werkzeug import urls, utils

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class EbizchargeController(http.Controller):
   # _approved_url = '/payment/ebizcharge/approved/'
    _approved_url = '/shop/confirmation/'
    _cancel_url = '/payment/ebizcharge/cancel/'
    _error_url = '/payment/ebizcharge/error'

    @http.route([
        '/shop/confirmation/',
        '/payment/ebizcharge/cancel/',
        '/payment/ebizcharge/error',
    ], type='http', auth='public', csrf=False)
    def ebizcharge_form_feedback(self, **post):
        #_logger.info('Ebizcharge: entering form_feedback with post data %s', pprint.pformat(post))
        return_url = '/'
        if post:
            request.env['payment.transaction'].sudo().form_feedback(post, 'ebizcharge')
            return_url = post.pop('return_url', '/shop/payment/validate')
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        _logger.info('Ebizcharge: entering form_feedback with post data %s', pprint.pformat(return_url))
        return request.render('payment_ebizcharge.payment_ebizcharge_redirect', {
            'return_url': urls.url_join(base_url, return_url)
        })
        #return werkzeug.utils.redirect(return_url)

    @http.route(['/payment/ebizcharge/s2s/create_json'], type='json', auth='public')
    def ebizcharge_s2s_create_json(self, **kwargs):
        acquirer_id = int(kwargs.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        if not kwargs.get('partner_id'):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        return acquirer.s2s_process(kwargs).id

    @http.route(['/payment/authorize/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def authorize_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        token = False
        acquirer = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id')))

        try:
            if not kwargs.get('partner_id'):
                kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
            token = acquirer.s2s_process(kwargs)
        except ValidationError as e:
            message = e.args[0]
            if isinstance(message, dict) and 'missing_fields' in message:
                msg = _("The transaction cannot be processed because some contact details are missing or invalid: ")
                message = msg + ', '.join(message['missing_fields']) + '. '
                if request.env.user._is_public():
                    message += _("Please sign in to complete your profile.")
                    # update message if portal mode = b2b
                    if request.env['ir.config_parameter'].sudo().get_param('auth_signup.allow_uninvited', 'False').lower() == 'false':
                        message += _("If you don't have any account, please ask your salesperson to update your profile. ")
                else:
                    message += _("Please complete your profile. ")

            return {
                'error': message
            }

        if not token:
            res = {
                'result': False,
            }
            return res

        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': False,
        }

        if verify_validity != False:
            token.validate()
            res['verified'] = token.verified

        return res

    @http.route(['/payment/ebizcharge/s2s/create'], type='http', auth='public')
    def ebizcharge_s2s_create(self, **post):
        acquirer_id = int(post.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        acquirer.s2s_process(post)
        return utils.redirect(post.get('return_url', '/'))
