# coding: utf-8

from werkzeug import urls
from datetime import datetime
import zeep
import hashlib
import hmac
import logging
import time

from odoo import _, api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_ebizcharge.controllers.main import EbizchargeController
from odoo.addons.payment_ebizcharge.models.ebizstub import *
from odoo.tools.float_utils import float_compare, float_repr
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class CustomerEbizcharge(models.Model):
    _inherit = 'res.partner'

    @api.model
    # def create(self, values):
    def create(self, values):
        wsdl = 'https://soap.ebizcharge.net/eBizService.svc?singleWsdl'
        client = zeep.Client(wsdl=wsdl)

        securityToken = {
                        "UserId":"magento2",
                        "SecurityId":"9ca3a18e-b8c4-4fad-bfb2-3cff4cdb7b86",
                        "Password" : "magento2"}

        customer = {
                    "FirstName" : "Mark",
                    "LastName" : "Wilson",
                    "CompanyName" : "CBS",
                    "CustomerId" : "C-E&000002",
                    "CellPhone" : "714-555-5014",
                    "Fax" : "714-555-5010",
                    "Phone" : "714-555-5015"}

        # result = client.service.AddCustomer('0814c940-5ea6-425e-8343-994c126caa13', 'magento2', 'magento2')
        result = client.service.AddCustomer(securityToken, customer)
        # credentials = self.env['payment.acquirer'].search([('id','=',13)])
        # # ebizcharge_security_id
        # # ebizcharge_user_id
        # # ebizcharge_password_id
        res = super(CustomerEbizcharge, self).create(values)
        return res

class PaymentAcquirerEbizcharge(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('ebizcharge', 'EBizCharge')])
    ebizcharge_security_id = fields.Char(string='SecurityId', required_if_provider='ebizcharge', groups='base.group_user')
    ebizcharge_user_id = fields.Char(string='UserId', required_if_provider='ebizcharge', groups='base.group_user')
    ebizcharge_password = fields.Char(string='Password', required_if_provider='ebizcharge', groups='base.group_user')

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * ebizcharge: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentAcquirerEbizcharge, self)._get_feature_support()
        res['authorize'].append('ebizcharge')
        #res['tokenize'].append('ebizcharge')
        return res

    def _get_ebizcharge_urls(self, environment):
        """ Authorize URLs """
        _logger.info(str(self.values))
        dat = ebiz_form_stub % self.values
        retxml= somereq("","",dat,"soap.ebizcharge.net","eBizService.svc","https")
        _logger.info(str(retxml))
        url= retxml.split("<GetEbizWebFormURLResult>")[1].split("</GetEbizWebFormURLResult>")[0]
        url= url.split("_")[0] 

        return {'ebizcharge_form_url': url}


    def _ebizcharge_generate_hashing(self, values):
        return ""

    def ebizcharge_form_generate_values(self, values):
        self.ensure_one()

        # State code is only supported in US, use state name by default
        state = values['partner_state'].name if values.get('partner_state') else ''
        if values.get('partner_country') and values.get('partner_country') == self.env.ref('base.us', False):
            state = values['partner_state'].code if values.get('partner_state') else ''
        billing_state = values['billing_partner_state'].name if values.get('billing_partner_state') else ''
        if values.get('billing_partner_country') and values.get('billing_partner_country') == self.env.ref('base.us', False):
            billing_state = values['billing_partner_state'].code if values.get('billing_partner_state') else ''

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        ebizcharge_tx_values = dict(values)
        temp_ebizcharge_tx_values = {
            'SecurityId': self.ebizcharge_security_id,
            'UserId': self.ebizcharge_user_id,
            'Password': self.ebizcharge_password,
            'x_amount': float_repr(values['amount'], values['currency'].decimal_places if values['currency'] else 2),
            'TransType': 'AUTH_CAPTURE' if self.capture_manually != 'ebizcharge' else 'AUTH_ONLY',
            'Sequence': '%s%s' % (self.id, int(time.time())),
            'Version': '1.0',
            'TimeStamp': datetime.now().strftime("%Y-%m-%dT00:00:00-00:00"),
            #'appurl': urlparse.urljoin(base_url, EbizchargeController._approved_url)+'?reference='+str(ebizcharge_tx_values["reference"])
            'appurl': urls.url_join(base_url, EbizchargeController._approved_url),
            #'appurl':'',
            #'decurl': urls.url_join(base_url, EbizchargeController._cancel_url),
            #'errurl': urls.url_join(base_url, EbizchargeController._error_url),
            'decurl':'',
            'errurl':'',
            'address': values.get('partner_address'),
            'city': values.get('partner_city'),
            'country': values.get('partner_country') and values.get('partner_country').name or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
            'phone': values.get('partner_phone'),
            'state': state,
            'billing_address': values.get('billing_partner_address'),
            'billing_city': values.get('billing_partner_city'),
            'billing_country': values.get('billing_partner_country') and values.get('billing_partner_country').name or '',
            'billing_email': values.get('billing_partner_email'),
            'billing_zip_code': values.get('billing_partner_zip'),
            'billing_first_name': values.get('billing_partner_first_name'),
            'billing_last_name': values.get('billing_partner_last_name'),
            'billing_phone': values.get('billing_partner_phone'),
            'billing_state': billing_state,
        }
        temp_ebizcharge_tx_values['returndata'] = ebizcharge_tx_values.pop('return_url', '')
        ebizcharge_tx_values.update(temp_ebizcharge_tx_values)
        self.values = ebizcharge_tx_values
        return ebizcharge_tx_values

    def ebizcharge_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_ebizcharge_urls(environment)['ebizcharge_form_url']
		

    @api.model
    def ebizcharge_s2s_form_process(self, data):
        values = {
            'cc_number': data.get('cc_number'),
            'cc_holder_name': data.get('cc_holder_name'),
            'cc_expiry': data.get('cc_expiry'),
            'cc_cvc': data.get('cc_cvc'),
            'cc_brand': data.get('cc_brand'),
            'acquirer_id': int(data.get('acquirer_id')),
            'partner_id': int(data.get('partner_id'))
        }
        PaymentMethod = self.env['payment.token'].sudo().create(values)
        return PaymentMethod

    def ebizcharge_s2s_form_validate(self, data):
        error = dict()
        mandatory_fields = ["cc_number", "cc_cvc", "cc_holder_name", "cc_expiry", "cc_brand"]
        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        if data['cc_expiry'] and datetime.now().strftime('%y%M') > datetime.strptime(data['cc_expiry'], '%M / %y').strftime('%y%M'):
            return False
        return False if error else True

    #def ebizcharge_test_credentials(self):
        #self.ensure_one()
        #transaction = AuthorizeAPI(self.acquirer_id)
        #return transaction.test_authenticate()

class TxAuthorize(models.Model):
    _inherit = 'payment.transaction'

    _ebizcharge_valid_tx_status = 1
    _ebizcharge_pending_tx_status = 4
    _ebizcharge_cancel_tx_status = 2

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def create(self, vals):
        # The reference is used in the Authorize form to fill a field (invoiceNumber) which is
        # limited to 20 characters. We truncate the reference now, since it will be reused at
        # payment validation to find back the transaction.
        if 'reference' in vals and 'acquirer_id' in vals:
            acquier = self.env['payment.acquirer'].browse(vals['acquirer_id'])
            if acquier.provider == 'ebizcharge':
                vals['reference'] = vals.get('reference', '')[:20]
        return super(TxAuthorize, self).create(vals)

    @api.model
    def _ebizcharge_form_get_tx_from_data(self, data):
        """ Given a data dict coming from ebizcharge, verify it and find the related
        transaction record. """
        _logger.info(data)
        reference = data.get("TransactionLookupKey")
        if not reference:
            error_msg = _('Authorize: received data with missing reference (%s)') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        tx = self.search([('reference', '=', reference)])
        _logger.info(str(tx))
        if not tx or len(tx) > 1:
            error_msg = 'Authorize: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    def _ebizcharge_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        #if self.acquirer_reference and data.get('x_trans_id') != self.acquirer_reference:
        #    invalid_parameters.append(('Transaction Id', data.get('TranRefNum'), self.acquirer_reference))
        # check what is buyed
        #if float_compare(float(data.get('x_amount', '0.0')), self.amount, 2) != 0:
        #    invalid_parameters.append(('Amount', data.get('x_amount'), '%.2f' % self.amount))
        return invalid_parameters

    def _ebizcharge_form_validate(self, data):
        self.write({'state': 'done',
                    'acquirer_reference': data.get('TranRefNum'),
                    'date_validate': fields.Datetime.now(),
                })
        return True

    def ebizcharge_s2s_do_transaction(self, **data):
        self.ensure_one()
        #transaction = AuthorizeAPI(self.acquirer_id)
        #if self.acquirer_id.auto_confirm != "ebizcharge":
            #res = transaction.auth_and_capture(self.payment_token_id, self.amount, self.reference)
        #else:
            #res = transaction.ebizcharge(self.payment_token_id, self.amount, self.reference)
        #return self._ebizcharge_s2s_validate_tree(res)

    #def ebizcharge_s2s_capture_transaction(self):
        #self.ensure_one()
        #transaction = AuthorizeAPI(self.acquirer_id)
        #tree = transaction.capture(self.acquirer_reference or '', self.amount)
        #return self._ebizcharge_s2s_validate_tree(tree)

    #def ebizcharge_s2s_void_transaction(self):
        #self.ensure_one()
        #transaction = AuthorizeAPI(self.acquirer_id)
        #tree = transaction.void(self.acquirer_reference or '')
        #return self._ebizcharge_s2s_validate_tree(tree)

    def _ebizcharge_s2s_validate_tree(self, tree):
        return self._ebizcharge_s2s_validate(tree)

    def _ebizcharge_s2s_validate(self, tree):
        self.ensure_one()
        if self.state in ['done', 'refunded']:
            _logger.warning('Authorize: trying to validate an already validated tx (ref %s)' % self.reference)
            return True
        status_code = int(tree.get('x_response_code', '0'))
        if status_code == self._ebizcharge_valid_tx_status:
            if tree.get('x_type').lower() in ['auth_capture', 'prior_auth_capture']:
                init_state = self.state
                self.write({
                    'state': 'done',
                    'acquirer_reference': tree.get('x_trans_id'),
                    'date_validate': fields.Datetime.now(),
                })
                if init_state != 'ebizcharged':
                    self.execute_callback()

                if self.payment_token_id:
                    self.payment_token_id.verified = True

            if tree.get('x_type').lower() == 'auth_only':
                self.write({
                    'state': 'authorized',
                    'acquirer_reference': tree.get('x_trans_id'),
                })
                self.execute_callback()
            if tree.get('x_type').lower() == 'void':
                if self.type == 'validation' and self.state == 'refunding':
                    self.write({
                        'state': 'refunded',
                    })
                else:
                    self.write({
                        'state': 'cancel',
                    })
            return True
        elif status_code == self._ebizcharge_pending_tx_status:
            new_state = 'refunding' if self.state == 'refunding' else 'pending'
            self.write({
                'state': new_state,
                'acquirer_reference': tree.get('x_trans_id'),
            })
            return True
        elif status_code == self._ebizcharge_cancel_tx_status:
            self.write({
                'state': 'cancel',
                'acquirer_reference': tree.get('x_trans_id'),
            })
            return True
        else:
            error = tree.get('x_response_reason_text')
            _logger.info(error)
            self.write({
                'state': 'error',
                'state_message': error,
                'acquirer_reference': tree.get('x_trans_id'),
            })
            return False

    _inherit = 'payment.token'

    ebizcharge_profile = fields.Char(string='Authorize.net Profile ID', help='This contains the unique reference '
                                    'for this partner/payment token combination in the Authorize.net backend')
    provider = fields.Selection(string='Provider', related='acquirer_id.provider')
    save_token = fields.Selection(string='Save Cards', related='acquirer_id.save_token')

    # @api.model
    # def ebizcharge_create(self, values):
    #     if values.get('cc_number'):
    #         values['cc_number'] = values['cc_number'].replace(' ', '')
    #         acquirer = self.env['payment.acquirer'].browse(values['acquirer_id'])
    #         expiry = str(values['cc_expiry'][:2]) + str(values['cc_expiry'][-2:])
    #         partner = self.env['res.partner'].browse(values['partner_id'])
    #         transaction = AuthorizeAPI(acquirer)
    #         res = transaction.create_customer_profile(partner, values['cc_number'], expiry, values['cc_cvc'])
    #         if res.get('profile_id') and res.get('payment_profile_id'):
    #             return {
    #                 'ebizcharge_profile': res.get('profile_id'),
    #                 'name': 'XXXXXXXXXXXX%s - %s' % (values['cc_number'][-4:], values['cc_holder_name']),
    #                 'acquirer_ref': res.get('payment_profile_id'),
    #             }
    #         else:
    #             raise ValidationError(_('The Customer Profile creation in Authorize.NET failed.'))
    #     else:
    #         return values