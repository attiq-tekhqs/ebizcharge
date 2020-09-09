import requests
import urllib.request, urllib.error, urllib.parse

def somereq(username, password, data, hostname, urlpath="", protocol="http"):
    url = "%s://%s/%s" % (protocol,hostname,urlpath)

    #create a password manager
    passManager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    passManager.add_password(None, url, username, password)

    #setup auth handler and opener
    authHandler = urllib.request.HTTPDigestAuthHandler(passManager)
    urlOpener = urllib.request.build_opener(authHandler)

    #set http headers
    #urlOpener.add_headers={'Host:':hostname ,'Content-Type': 'text/xml;charset=UTF-8','SOAPAction':'"http://eBizCharge.ServiceModel.SOAP/IeBizService/GetEbizWebFormURL"','Content-Length':str(len(data)),'Accept-Encoding':'gzip,deflate'}
    headers={'Host':hostname,'SOAPAction':'"http://eBizCharge.ServiceModel.SOAP/IeBizService/GetEbizWebFormURL"','Content-Length':str(len(data)),'Content-Type':'text/xml;charset=utf-8'}

    #send request
    try:

      data = data.encode("utf-8")

      request = urllib.request.Request(url,data=data,headers=headers)
      req = urllib.request.urlopen(request)
      #read and return result
      result=req.read().decode('utf-8')
      #response = requests.post(url, data=data, headers=headers)
    except urllib.error.HTTPError as error:
      result = error.read()
    return result

ebiz_form_stub = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ebiz="http://eBizCharge.ServiceModel.SOAP">
   <soapenv:Header/>
   <soapenv:Body>
      <ebiz:GetEbizWebFormURL>
         <ebiz:securityToken>
            <ebiz:SecurityId>%(SecurityId)s</ebiz:SecurityId>
            <ebiz:UserId>%(UserId)s</ebiz:UserId>
            <ebiz:Password>%(Password)s</ebiz:Password>
         </ebiz:securityToken>
         <ebiz:ePaymentForm>
            <ebiz:FormType>Webform</ebiz:FormType>
            <ebiz:EmailAddress>%(email)s</ebiz:EmailAddress>
            <ebiz:ReplyToDisplayName>%(billing_partner_name)s</ebiz:ReplyToDisplayName>
            <ebiz:SendEmailToCustomer>true</ebiz:SendEmailToCustomer>
            <ebiz:CustomerId>%(partner_id)s</ebiz:CustomerId>
            <ebiz:CustFullName>%(billing_partner_name)s</ebiz:CustFullName>
            <ebiz:TransId></ebiz:TransId>
            <ebiz:TransDetail>Payement</ebiz:TransDetail>
            <ebiz:InvoiceNumber>Inv</ebiz:InvoiceNumber>
            <ebiz:PoNum>Po</ebiz:PoNum>
            <ebiz:SoNum>So</ebiz:SoNum>
            <ebiz:OrderId>O</ebiz:OrderId>
            <ebiz:Date>%(TimeStamp)s</ebiz:Date>
            <ebiz:DueDate>%(TimeStamp)s</ebiz:DueDate>
            <ebiz:TotalAmount>%(amount)s</ebiz:TotalAmount>
            <ebiz:AmountDue>%(amount)s</ebiz:AmountDue>
            <ebiz:ShippingAmount>0</ebiz:ShippingAmount>
            <ebiz:DutyAmount>0</ebiz:DutyAmount>
            <ebiz:TaxAmount>0</ebiz:TaxAmount>
            <ebiz:Description>Payment</ebiz:Description>
            <ebiz:BillingAddress>
               <ebiz:FirstName>%(first_name)s</ebiz:FirstName>
               <ebiz:LastName>%(last_name)s</ebiz:LastName>
               <ebiz:Address1>%(billing_address)s</ebiz:Address1>
               <ebiz:City>%(billing_city)s</ebiz:City>
               <ebiz:State>%(billing_state)s</ebiz:State>
               <ebiz:ZipCode>%(billing_zip_code)s</ebiz:ZipCode>
               <ebiz:Country>USA</ebiz:Country>
            </ebiz:BillingAddress>
            <ebiz:ShippingAddress>
               <ebiz:FirstName>%(first_name)s</ebiz:FirstName>
               <ebiz:LastName>%(last_name)s</ebiz:LastName>
               <ebiz:Address1>%(address)s</ebiz:Address1>
               <ebiz:City>%(city)s</ebiz:City>
               <ebiz:State>%(state)s</ebiz:State>
               <ebiz:ZipCode>%(zip_code)s</ebiz:ZipCode>
               <ebiz:Country>USA</ebiz:Country>
            </ebiz:ShippingAddress>
            <ebiz:ApprovedURL>%(appurl)s</ebiz:ApprovedURL>
            <ebiz:DeclinedURL>%(decurl)s</ebiz:DeclinedURL>
            <ebiz:ErrorURL>%(errurl)s</ebiz:ErrorURL>
            <ebiz:DisplayDefaultResultPage>0</ebiz:DisplayDefaultResultPage>
            <ebiz:SavePaymentMethod>true</ebiz:SavePaymentMethod>
            <ebiz:ShowSavedPaymentMethods>true</ebiz:ShowSavedPaymentMethods>
            <ebiz:CountryCode>USA</ebiz:CountryCode>
            <ebiz:CurrencyCode>USD</ebiz:CurrencyCode>
            <ebiz:ProcessingCommand>Sale</ebiz:ProcessingCommand>
            <ebiz:SoftwareId>Odoo</ebiz:SoftwareId>
            <ebiz:TransactionLookupKey>%(reference)s</ebiz:TransactionLookupKey>
            <ebiz:Clerk>User1</ebiz:Clerk>
            <ebiz:Terminal>Web1</ebiz:Terminal>
         </ebiz:ePaymentForm>
      </ebiz:GetEbizWebFormURL>
   </soapenv:Body>
</soapenv:Envelope>"""

if __name__=="__main__":
    import requests
    formdict =  {
       'appurl':'http://198.27.119.65:8069/payment/ebizcharge/approved/',
       'last_name':'Administrator',
       'decurl':'http://198.27.119.65:8069/payment/ebizcharge/cancel/',
       'reference':'SO013x1',
       'billing_partner_id':3,
       'billing_partner_name':'Administrator',
       'address':'215 Vine St',
       'billing_partner_address':'215 Vine St',
       'billing_city':'Scranton',
       'currency_id':3,
       'Version':'1.0',
       'partner_id':3,
       'billing_country':'United States',
       'billing_last_name':'Administrator',
       'billing_partner_city':'Scranton',
       'city':'Scranton',
       'first_name':'',
       'partner_name':'Administrator',
       'billing_email':'schapman1974@gmail.com',
       'billing_partner_last_name':'Administrator',
       'billing_phone':'+1 555-555-5555',
       'state':'PA',
       'partner_lang':'en_US',
       'Password':'Odoo7852!',
       'partner_country_id':235,
       'zip_code':'18503',
       'partner_address':'215 Vine St',
       'billing_partner_country_id':235,
       'partner_email':'schapman1974@gmail.com',
       'billing_address':'215 Vine St',
       'billing_first_name':'',
       'returndata':'/shop/payment/validate',
       'TransType':'AUTH_CAPTURE',
       'billing_partner_lang':'en_US',
       'phone':'+1 555-555-5555',
       'TimeStamp':'2017-04-19T07:38:57-07:00',
       'UserId':'Odoo1',
       'partner_zip':'18503',
       'billing_zip_code':'18503',
       'errurl':'http://198.27.119.65:8069/payment/ebizcharge/error',
       'partner_first_name':'',
       'billing_partner_first_name':'',
       'billing_partner_zip':'18503',
       'Sequence':'201513816421',
       'amount':16.5,
       'partner_city':'Scranton',
       'Amount':'16.5',
       'billing_partner_email':'schapman1974@gmail.com',
       'email':'schapman1974@gmail.com',
       'partner_last_name':'Administrator',
       'partner_phone':'+1 555-555-5555',
       'SecurityId':'0814c940-5ea6-425e-8343-994c126caa13',
       'billing_state':'PA',
       'country':'United States',
       'billing_partner_phone':'+1 555-555-5555'
    }
    dat = ebiz_form_stub % formdict
    retxml= somereq("","",dat,"soap.ebizcharge.net","eBizService.svc","https")
    #req = requests.post("https://soap.ebizcharge.net/eBizService.svc",data=dat)
    #print req.text
    url= retxml.split("<GetEbizWebFormURLResult>")[1].split("</GetEbizWebFormURLResult>")[0]
    print(url)
