
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


    @http.route('/financial/data', auth='public')
    def directories(self, **kw):
        
        
        if 'id' in kw:
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
                  AND line.id = 1
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
                      and aa.company_id = 1
                          LEFT join account_account_type aat 
                      on aat.id = aa.user_type_id

                    LEFT join account_move_line aml 
                      on aml.account_id = aa.id
                        and aml.date between '2019-01-01' and '2020-12-01'

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

            cr2.execute(sql2)
            result2 = cr2.dictfetchall()
          
          
            data=[]
            
            for dir in result2:
                    data.append({
                          'id': dir['id_first'] + 1000,
                          'name': dir['name'],
                          'state': 'open',
                          'parentId': dir['id_first'],
                          'balance' :dir['balance'],
                      })
            
        else:
            """ ///////////////////////////////////////////////////////////////////////////////////////"""
            
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
                  AND line.id = 1
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

            cr.execute(sql)
            result = cr.dictfetchall()
            
            """ ///////////////////////////////////////////////////////////////////////////////////////"""
            
            
            
            data=[]

            for dir in result:
                    data.append({
                          'id': dir['id_first'],
                          'name': dir['parent_name'],
                          'state': 'closed',
                          'parentId': dir['parent_id'],
                      })
            
                    
                    
     

        return simplejson.dumps(data)
