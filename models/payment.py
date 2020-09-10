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


''' Not required for Invoice sync in Ebizcharge at Create '''
class InvoiceEbizcharge(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, values):
        print("In Invoice create")
        res = super(InvoiceEbizcharge, self).create(values)

        wsdl = 'https://soap.ebizcharge.net/eBizService.svc?singleWsdl'
        client = zeep.Client(wsdl=wsdl)

        securityToken = {
            "UserId": self.ebizcharge_user_id,
            "SecurityId": self.ebizcharge_security_id,
            "Password": self.ebizcharge_password
        }

        try:
            get_response = client.service.GetCustomer(securityToken, "", values['partner'].ebizcharge_customer_id)
        except:
            billingAddress = {
                "Address1": values['billing_partner_address'],
                "City": values['billing_partner_city'],
                "ZipCode": values['billing_partner_zip'],
                "State": values['partner_state'].display_name
            }

            customer = {
                "FirstName": values['partner_first_name'],
                "LastName": values['partner_last_name'],
                "Email": values['partner_email'],
                "CustomerId": values['partner_id'],
                # "CompanyName": values[''],
                "Phone": values['partner_phone'],
                "BillingAddress": billingAddress
            }

            add_response = client.service.AddCustomer(securityToken, customer)

            if not add_response['Error']:
                odoo_customer = self.env['res.partner'].search([('id', '=', add_response['CustomerId'])])
                # odoo_customer = self.env['res.partner'].search([('id', '=', values['partner_id'])])
                odoo_customer.write({
                    'ebizcharge_customer_id': add_response['CustomerInternalId'],
                })
                self.env.cr.commit()

        ''' Get customer through id '''

        return res

''' Not required for Customer sync in Ebizcharge at Create '''
class CustomerEbizcharge(models.Model):
    _inherit = 'res.partner'

    '''  Correct fields  '''
    # ebizcharge_customer_id = fields.Char(string='Customer Id', required=False)
    # ebizcharge_customer_internal_id = fields.Char(string='Customer Internal Id', required=False)
    # ebizcharge_customer_token = fields.Char(string='Customer Token', required=False)

    ebizcharge_customer_id = fields.Char(string='Customer Internal Id', required=False)
    ebizcharge_security_token = fields.Char(string='Security Token', required=False)

    '''  Create Override  '''
    # @api.model
    # # def create(self, values):
    # def create(self, values):
    #     res = super(CustomerEbizcharge, self).create(values)
    #
    #     # credentials = self.env['payment.acquirer'].search([('id','=',13)])
    #     # # ebizcharge_security_id
    #     # # ebizcharge_user_id
    #     # # ebizcharge_password_id
    #
    #     wsdl = 'https://soap.ebizcharge.net/eBizService.svc?singleWsdl'
    #     client = zeep.Client(wsdl=wsdl)
    #
    #     # securityToken = {
    #     #                 "UserId":"magento2",
    #     #                 "SecurityId":"9ca3a18e-b8c4-4fad-bfb2-3cff4cdb7b86",
    #     #                 "Password" : "magento2"}
    #
    #     getSecurityToken = {
    #         "UserId": "",
    #         "SecurityId": "9ca3a18e-b8c4-4fad-bfb2-3cff4cdb7b86",
    #         "Password": ""}
    #
    #     '''  Test Code  '''
    #     # customer = {
    #     #             "FirstName" : "Mark",
    #     #             "LastName" : "Wilson",
    #     #             "CompanyName" : "CBS",
    #     #             "CustomerId" : "C-E&000002",
    #     #             "CellPhone" : "714-555-5014",
    #     #             "Fax" : "714-555-5010",
    #     #             "Phone" : "714-555-5015"}
    #
    #     # customer = {
    #     #             "FirstName": res.name,
    #     #             "CustomerId": res.id,
    #     #             "CellPhone": res.mobile,
    #     #             "Phone": res.phone}
    #     #
    #     # result = client.service.AddCustomer(securityToken, customer)
    #     get_result = client.service.GetCustomer(getSecurityToken, "C-E&000002", "")
    #
    #     return res


class PaymentAcquirerEbizcharge(models.Model):
    _inherit = 'payment.acquirer'

    '''  Last Sync memory  '''
    # ebizcharge_last_sync = fields.Datetime(string='Last Sync Date', readonly=True)
    provider = fields.Selection(selection_add=[('ebizcharge', 'EBizCharge')])
    ebizcharge_security_id = fields.Char(string='SecurityId', required_if_provider='ebizcharge', groups='base.group_user')
    ebizcharge_user_id = fields.Char(string='UserId', required_if_provider='ebizcharge', groups='base.group_user')
    ebizcharge_password = fields.Char(string='Password', required_if_provider='ebizcharge', groups='base.group_user')
    ebizcharge_sync = fields.Boolean(string='EBizCharge Syncing', groups='base.group_user')

    def upload_invoices(self):
        print("Upload invoices functionality")

        # if self.state == 'enabled':
        #     wsdl = 'https://soap.ebizcharge.net/eBizService.svc?singleWsdl'
        #     client = zeep.Client(wsdl=wsdl)
        #
        #     securityToken = {
        #         "UserId": self.ebizcharge_user_id,
        #         "SecurityId": self.ebizcharge_security_id,
        #         "Password": self.ebizcharge_password
        #     }
        #
        #     ''' Get all invoices greater than Last Sync date/time  '''
        #     #  For Now its getting all available invoices
        #     invoices = self.env['account.move'].search([])
        #
        #     for invoice in invoices:
        #         print(invoice.id)
        #
        #         '''  Dict For testing  '''
        #         # dummy_invoice = {
        #         #     "CustomerId": "C-E&000002",
        #         #     "SubCustomerId": "",
        #         #     "InvoiceNumber": "00102565",
        #         #     "InvoiceDate": "04/02/2016",
        #         #     "InvoiceDueDate": "08/12/2016",
        #         #     "InvoiceAmount": 2000.45,
        #         #     "AmountDue": 200.45,
        #         #     "DivisionId": "001",
        #         #     "PoNum": "Po001",
        #         #     "SoNum": "",
        #         #     "NotifyCustomer": 0
        #         # }
        #
        #         invoice_dict = {
        #             "CustomerId": invoice.partner_id.id,
        #             "SubCustomerId": "",
        #             "InvoiceNumber": invoice.name,
        #             "InvoiceDate": invoice.invoice_date if invoice.invoice_date else "",
        #             "InvoiceDueDate": invoice.invoice_date_due if invoice.invoice_date_due else "",
        #             "InvoiceAmount": invoice.amount_total,
        #             "AmountDue": invoice.amount_residual,
        #             "DivisionId": "",
        #             "PoNum": "",
        #             "SoNum": "",
        #             "NotifyCustomer": 0
        #         }
        #
        #         res = client.service.AddInvoice(securityToken, invoice_dict)

        return self.action_of_button()

    def action_of_button(self):
        # do what ever login like in your case send an invitation
        ...
        ...
        # don't forget to add translation support to your message _()
        message_id = self.env['message.wizard'].create({'text': "Upload Invoices Successfully."})
        return {
            'name': 'Successfull',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new',
        }

        '''  Update Last sync date/time here  '''

        '''  Add customer if not exists in Ebizcharge  '''
        # try:
            #     get_response = client.service.GetCustomer(securityToken, "", values['partner'].ebizcharge_customer_id)
            # except:
            #     billingAddress = {
            #         "Address1": values['billing_partner_address'],
            #         "City": values['billing_partner_city'],
            #         "ZipCode": values['billing_partner_zip'],
            #         "State": values['partner_state'].display_name
            #     }
            #
            #     customer = {
            #         "FirstName": values['partner_first_name'],
            #         "LastName": values['partner_last_name'],
            #         "Email": values['partner_email'],
            #         "CustomerId": values['partner_id'],
            #         # "CompanyName": values[''],
            #         "Phone": values['partner_phone'],
            #         "BillingAddress": billingAddress
            #     }
            #
            #     add_response = client.service.AddCustomer(securityToken, customer)
            #
            #     if not add_response['Error']:
            #         odoo_customer = self.env['res.partner'].search([('id', '=', add_response['CustomerId'])])
            #         # odoo_customer = self.env['res.partner'].search([('id', '=', values['partner_id'])])
            #         odoo_customer.write({
            #             'ebizcharge_customer_id': add_response['CustomerInternalId'],
            #         })
            #         self.env.cr.commit()




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
        # res['tokenize'].append('ebizcharge')
        return res

    def _get_ebizcharge_urls(self, environment):
        """ Authorize URLs """
        _logger.info(str(self.values))
        dat = ebiz_form_stub % self.values
        retxml = somereq("", "", dat, "soap.ebizcharge.net", "eBizService.svc", "https")
        _logger.info(str(retxml))
        url = retxml.split("<GetEbizWebFormURLResult>")[1].split("</GetEbizWebFormURLResult>")[0]
        url = url.split("_")[0]

        return {'ebizcharge_form_url': url}

    def _ebizcharge_generate_hashing(self, values):
        return ""

    ''' New implementation  '''

    def ebizcharge_customer(self, values):
        self.ensure_one()

        wsdl = 'https://soap.ebizcharge.net/eBizService.svc?singleWsdl'
        client = zeep.Client(wsdl=wsdl)

        ''' Get request token'''
        # getSecurityToken = {
        #     "UserId": self.ebizcharge_user_id,
        #     "SecurityId": self.ebizcharge_security_id,
        #     "Password": self.ebizcharge_password}

        '''  Test case to add customer  '''
        # dummy_customer = {
        #     "FirstName": values['partner_first_name'],
        #     "LastName": values['partner_last_name'],
        #     "CustomerId": 341,
        #     # "CompanyName": company_name,
        #     "Phone": values['partner_phone'],
        #     "BillingAddress": billingAddress
        # }

        '''  Correct implementation of addCustomer  '''
        securityToken = {
            "UserId": self.ebizcharge_user_id,
            "SecurityId": self.ebizcharge_security_id,
            "Password": self.ebizcharge_password
        }

        try:
            client.service.GetCustomer(securityToken, "", values['partner'].ebizcharge_customer_id)
        except:
            billingAddress = {
                "Address1": values['billing_partner_address'],
                "City": values['billing_partner_city'],
                "ZipCode": values['billing_partner_zip'],
                "State": values['partner_state'].display_name
            }

            customer = {
                "FirstName": values['partner_first_name'],
                "LastName": values['partner_last_name'],
                "Email": values['partner_email'],
                "CustomerId": values['partner_id'],
                # "CompanyName": values[''],
                "Phone": values['partner_phone'],
                "BillingAddress": billingAddress
            }

            add_response = client.service.AddCustomer(securityToken, customer)

            if not add_response['Error']:
                odoo_customer = self.env['res.partner'].search([('id', '=', add_response['CustomerId'])])
                # odoo_customer = self.env['res.partner'].search([('id', '=', values['partner_id'])])
                odoo_customer.write({
                    'ebizcharge_customer_id': add_response['CustomerInternalId'],
                })
                self.env.cr.commit()


        '''  SearchCustomerList implementation  '''
        # searchFilter = {
        #     "FieldName": "CustomerId",
        #     "ComparisonOperator": "eq",
        #     'FieldValue': values['partner_id']
        # }
        #
        # # complex_filter = [{
        # #     "filter":
        # #     [{
        # #     "FieldName": "CustomerId",
        # #     "FieldValue": "3",
        # #     "ComparisonOperator": "eq",
        # #     }]
        # # }]
        #
        # securityToken = {
        #     "UserId": self.ebizcharge_user_id,
        #     "SecurityId": self.ebizcharge_security_id,
        #     "Password": self.ebizcharge_password}
        #
        # filter = {
        #     "SearchFilter": {
        #         "FieldName": "CustomerId",
        #         "ComparisonOperator": "eq",
        #         "FieldValue": "3"
        #     }
        # }
        #
        # complex_filter = {
        #     "FieldName": "CustomerId",
        #     "ComparisonOperator": "eq",
        #     "FieldValue": "3"
        # }
        #
        # ''' According to  PHP implementation  '''
        # code_filters = {
        #     "FieldName": "Email",
        #     "ComparisonOperator": "eq",
        #     "FieldValue": values['partner_email']
        # }
        #
        # params = {
        #     "securityToken": securityToken,
        #     "filters": {"SearchFilter": code_filters},
        #     "includeCustomerToken": 1,
        #     "includePaymentMethodProfiles": 0,
        #     "countOnly": 0,
        #     "start": 0,
        #     "limit": 10
        # }
        #
        # params1 = [
        #     securityToken,
        #     {"SearchFilter": complex_filter},
        #     1,
        #     0,
        #     0,
        #     0,
        #     10]
        #
        # params2 = [
        #     securityToken,
        #     complex_filter,
        #     1,
        #     0,
        #     0,
        #     0,
        #     10]
        #
        # # get_result = client.service.GetCustomer(getSecurityToken, values['partner_id'], "")
        # try:
        #     new_search_customer = client.service.SearchCustomerList(securityToken, filter, 1, 0, 0, 0, 0, 100)
        #     search_customer = client.service.SearchCustomerList(securityToken, complex_filter, 1, 0, 0, 0, 100)
        #     # search_customer = client.service.SearchCustomerList(params)
        #     get_result = client.service.GetCustomer(securityToken, "3", "")
        #     search_customers = client.service.SearchCustomers(securityToken, "", "3", 0, 100, "Saeed")
        # except:
        #
        #     customer = {
        #         "FirstName": values['partner_first_name'],
        #         "LastName": values['partner_last_name'],
        #         "CustomerId": values['partner_id'],
        #         # "CompanyName": company_name,
        #         "Phone": values['partner_phone']}
        #
        #     result = client.service.AddCustomer(securityToken, customer)
        #
        #     odoo_customer = self.env['res.partner'].search([('id', '=', result['CustomerId'])])
        #
        #     odoo_customer.write({
        #         'ebizcharge_customer_id': result['CustomerInternalId'],
        #         # 'ebizcharge_security_token': result['CustomerToken']
        #     })
        #     self.env.cr.commit()
        #     print("No record Found")
        # print("Out of Get Request")
        # # addSecurityToken = {
        # #     "UserId": self.ebizcharge_user_id,
        # #     "SecurityId": self.ebizcharge_security_id,
        # #     "Password": self.ebizcharge_password}
        #
        # ''' For company  '''
        # # if values['partner_company_name']:
        # #     company_name = values['partner_company_name']
        # # else:
        # #     company_name = ""
        #
        # # customer = {
        # #             "FirstName": values['partner_first_name'],
        # #             "LastName": values['partner_last_name'],
        # #             "CustomerId": values['partner_id'],
        # #             # "CompanyName": company_name,
        # #             "Phone": values['partner_phone'],}
        #
        # # result = client.service.AddCustomer(addSecurityToken, customer)
        # print("Testing")

    def ebizcharge_form_generate_values(self, values):
        self.ensure_one()

        '''Comment For Testing'''
        self.ebizcharge_customer(values)

        # State code is only supported in US, use state name by default
        state = values['partner_state'].name if values.get('partner_state') else ''
        if values.get('partner_country') and values.get('partner_country') == self.env.ref('base.us', False):
            state = values['partner_state'].code if values.get('partner_state') else ''
        billing_state = values['billing_partner_state'].name if values.get('billing_partner_state') else ''
        if values.get('billing_partner_country') and values.get('billing_partner_country') == self.env.ref('base.us',
                                                                                                           False):
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
            # 'appurl': urlparse.urljoin(base_url, EbizchargeController._approved_url)+'?reference='+str(ebizcharge_tx_values["reference"])
            'appurl': urls.url_join(base_url, EbizchargeController._approved_url),
            # 'appurl':'',
            # 'decurl': urls.url_join(base_url, EbizchargeController._cancel_url),
            # 'errurl': urls.url_join(base_url, EbizchargeController._error_url),
            'decurl': '',
            'errurl': '',
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
            'billing_country': values.get('billing_partner_country') and values.get(
                'billing_partner_country').name or '',
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
        # self.ensure_one()
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
        if data['cc_expiry'] and datetime.now().strftime('%y%M') > datetime.strptime(data['cc_expiry'],
                                                                                     '%M / %y').strftime('%y%M'):
            return False
        return False if error else True

    # def ebizcharge_test_credentials(self):
    # self.ensure_one()
    # transaction = AuthorizeAPI(self.acquirer_id)
    # return transaction.test_authenticate()


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

        # if self.acquirer_reference and data.get('x_trans_id') != self.acquirer_reference:
        #    invalid_parameters.append(('Transaction Id', data.get('TranRefNum'), self.acquirer_reference))
        # check what is buyed
        # if float_compare(float(data.get('x_amount', '0.0')), self.amount, 2) != 0:
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
        # transaction = AuthorizeAPI(self.acquirer_id)
        # if self.acquirer_id.auto_confirm != "ebizcharge":
        # res = transaction.auth_and_capture(self.payment_token_id, self.amount, self.reference)
        # else:
        # res = transaction.ebizcharge(self.payment_token_id, self.amount, self.reference)
        # return self._ebizcharge_s2s_validate_tree(res)

    # def ebizcharge_s2s_capture_transaction(self):
    # self.ensure_one()
    # transaction = AuthorizeAPI(self.acquirer_id)
    # tree = transaction.capture(self.acquirer_reference or '', self.amount)
    # return self._ebizcharge_s2s_validate_tree(tree)

    # def ebizcharge_s2s_void_transaction(self):
    # self.ensure_one()
    # transaction = AuthorizeAPI(self.acquirer_id)
    # tree = transaction.void(self.acquirer_reference or '')
    # return self._ebizcharge_s2s_validate_tree(tree)

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