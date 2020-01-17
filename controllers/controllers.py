
from odoo import http
import simplejson
import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)

class financialStatement(http.Controller):

    @http.route('/financial/index', auth='user',website=True)
    def index(self, **kw):
        return http.request.render('vit_financial_statements.index', {
        })
        
    @http.route('/financial/company', auth='public', csrf=False)
    def get_company(self):
        company = http.request.env['res.company'].search_read([], fields=['id','name'])
        data= []
        for dir in company :
            data.append({
                'id': dir['id'],
                'text': dir['name'],
            })
            
        return simplejson.dumps(data)  
      
    @http.route('/financial/report', auth='public', csrf=False)
    def get_report(self):
        report = http.request.env['vit_financial_statements'].search_read([('parent_id','=', False)], fields=['id','name'])
        data= []
        for dir in report :
            data.append({
                'id': dir['id'],
                'text': dir['name'],
            })
            
        return simplejson.dumps(data)  


    @http.route('/financial/data', auth='public')
    def directories(self,**kw):
      
        if 'report_id' in kw:
          report_id = kw['report_id']
        else :
          report_id = 0

        if 'company_id' in kw:
          company_id = kw['company_id']
          
        if 'date_start' in kw:
          date_start = datetime.datetime.strptime(kw['date_start'], '%m/%d/%Y').strftime('%Y/%m/%d') # merubah format tanggal

          
        if 'date_end' in kw:
          date_end = datetime.datetime.strptime(kw['date_end'], '%m/%d/%Y').strftime('%Y/%m/%d') # merubah format tanggal

        
        if 'id' in kw:
          
            directory_id = int(kw['id'])
            sql2 = """
                WITH RECURSIVE parent (id, parent_id, code, name, level, criteria, source) AS (
                SELECT
                  line.id,
                  line.parent_id,
                  line.code,
                  line.name,
                  line.level,
                  line.criteria,
                  line.source,
                  array[line.id] as path_info
                FROM
                  vit_financial_statements as line
                WHERE
                  line.parent_id is NULL
                  AND line.id = %s
                UNION ALL
                  SELECT
                    child.id,
                    child.parent_id,
                    child.code,
                    child.name,
                    child.level,
                    child.criteria,
                    child.source,
                    parent.path_info||child.id
                  FROM
                    vit_financial_statements as child
                  INNER JOIN parent ON child.parent_id = parent.id
                ) SELECT
                    parent.id as id_first,
                    parent.level,
                    parent.name as parent_name,
                    parent.criteria,
                    parent.code,
                    path_info,
                    parent.parent_id,
                    parent.source,
                    aat.name,
                    aa.id,
                    aa.name,
                    aa.code,
                    case 
                    when aat.name in ('Income','Other Income','Equity','Payable','Credit Card','Current Liabilities','Non-current Liabilities') then
                        sum(coalesce(aml.credit,0) - coalesce(aml.debit,0)) 
                    else
                        sum(coalesce(aml.debit,0) - coalesce(aml.credit,0))
                end as balance
                FROM
                    parent
                    LEFT JOIN account_account aa  
                      on aa.code like parent.criteria
                      and aa.company_id = %s
                          LEFT join account_account_type aat 
                      on aat.id = aa.user_type_id

                    LEFT join account_move_line aml 
                      on aml.account_id = aa.id
                        and aml.date between %s and %s

                    LEFT join account_move am
                        on aml.move_id = am.id 
                        and am.state = 'posted'

                        where balance != 0
                group by 
                    parent.id,
                    parent.level,
                    parent.name,
                    parent.criteria,
                    parent.code,
                    path_info,
                    parent.parent_id,
                    parent.source,
                    aat.name,
                    aa.id,
                    aa.name,
                    aa.code
                order by path_info
            """
            
            cr2 = http.request.env.cr
            
            cr2.execute(sql2, (report_id,company_id,date_start,date_end))
            result2 = cr2.dictfetchall()
            result = []
   
        else:
            directory_id = False
            
            
            sql =""" WITH RECURSIVE parent (id, parent_id, code, name, level, criteria, source) AS (
                SELECT
                  line.id,
                  line.parent_id,
                  line.code,
                  line.name,
                  line.level,
                  line.criteria,
                  line.source,
                  array[line.id] as path_info
                FROM
                  vit_financial_statements as line
                WHERE
                  line.parent_id is NULL
                  AND line.id = %s
                UNION ALL
                  SELECT
                     child.id,
                     child.parent_id,
                     child.code,
                     child.name,
                     child.level,
                     child.criteria,
                     child.source,
                     parent.path_info||child.id
                  FROM
                     vit_financial_statements as child
                  INNER JOIN parent ON child.parent_id = parent.id
                ) SELECT
                    parent.id as id_first,
                    parent.level,
                    parent.name as parent_name,
                    parent.criteria,
                    parent.code,
                    path_info,
                    parent.parent_id,
                    parent.source
                FROM
                    parent
                where parent_id != 0
                  
                group by 
                    parent.id,
                    parent.level,
                    parent.name,
                    parent.criteria,
                    parent.code,
                    path_info,
                    parent.parent_id,
                    parent.source
                order by path_info
            
            """
            
            cr = http.request.env.cr

            cr.execute(sql,(report_id,))
            result = cr.dictfetchall()
            result2 = []
            
            
            
            
        data=[]

        for dir in result:
            balance = 0
            idlevel1 = dir['id_first']
          
            sql3 = """
            SELECT
                    vfs.id,
                    vfs.code,
                    vfs.name as parent_name,
                    ( select 
                            case 
                            when aat.name in ('Income','Other Income','Equity','Payable','Credit Card','Current Liabilities','Non-current Liabilities') then
                                sum(coalesce(aml.credit,0) - coalesce(aml.debit,0)) 
                            else
                                sum(coalesce(aml.debit,0) - coalesce(aml.credit,0))
                            end 
                    FROM
                    vit_financial_statements vfs
                    
                    LEFT JOIN account_account aa  
                      on aa.code like vfs.criteria
                      and aa.company_id = 1
                          LEFT join account_account_type aat 
                      on aat.id = aa.user_type_id

                    LEFT join account_move_line aml 
                      on aml.account_id = aa.id
                        and aml.date between '2019-01-01' and '2020-12-01'

                    LEFT join account_move am
                        on aml.move_id = am.id 
                        and am.state = 'posted'

                    where vfs.id = %s
                        group by 
                            aat.name
                            ) as balance
                    
                    FROM
                        vit_financial_statements vfs

                    where vfs.id = %s
            
            """

            cr3 = http.request.env.cr

            cr3.execute(sql3, (idlevel1, idlevel1,))
            result3 = cr3.dictfetchall()
            
          
            for dirs in result3 :
              if dirs['code'] == 'sale' :
                balance_sales = dirs['balance']
              else :
                balance_sales = 0
                
              if dirs['code'] == 'HPP'  :
                balance_COGS = dirs['balance']
              else :
                balance_COGS = 0
                
              if dirs['code'] == 'ADM' :
                balance_admin = dirs['balance']
              else :
                balance_admin = 0
                
              if dirs['code'] == 'OTHER' :
                balance_other = dirs['balance']
              else :
                balance_other = 0
# ///////////////////////////////////////////////////////////////////////////////
                
            if balance_sales != 0 :
              balance_sales_nilai = balance_sales
 
            if balance_COGS != 0 :
              balance_COGS_nilai = balance_COGS
              
            if balance_admin != 0 :
              balance_admin_nilai = balance_admin
              
            if balance_other != 0 :
              balance_other_nilai = balance_other
              
            if dirs['code'] == 'GROSS' :
              balance = balance_sales_nilai + balance_COGS_nilai
            elif dirs['code'] == 'NP' :
              balance = (balance_sales_nilai + balance_COGS_nilai) + balance_admin - balance_other
            else :
              balance = dirs['balance']
              
            data.append({
                  'id': dir['id_first'],
                  'name': dir['parent_name'],
                  'state': 'closed',
                  'parentId': str(directory_id),
                  'balance' : balance
              })
            
        for dir in result2:
            parent_id = dir['id_first']
            if directory_id == parent_id :
              data.append({
                    'id': dir['id_first'],
                    'name': dir['name'],
                    'state': 'open',
                    'parentId': parent_id,
                    'balance' :dir['balance'],
                })
            
            
            
            
        return simplejson.dumps(data)
