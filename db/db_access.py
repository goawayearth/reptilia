import logging
import pymssql

logger = logging.getLogger(__name__)


#  在股票历史价格表中传入数据
def insert_hisq_data(row):

    # 1. 建立数据库连接
    connection = pymssql.connect(host='localhost',
                           server='LAPTOP-',# 修改
                           port='1433',
                           user='sa', password='123456',# 修改
                           database='NASDAQ',
                           charset='GBK',
                           autocommit=True)
    if connection:
        print('数据库连接!')
    try:
        # 2. 创建游标对象
        with connection.cursor() as cursor:

            sql = "insert into HistoricalQuote (HDate,Open1,High,Low,Close1,Volume,Symbol)" \
                  "values (%(Date)s,%(Open)s,%(High)s,%(Low)s,%(Close)s,%(Volume)s,%(Symbol)s)"
            cursor.execute(sql,row)
            connection.commit()
            print('数据插入成功!')
    except pymssql.DatabaseError as error:
        connection.rollback()
        print(error)

    finally:
        connection.close()
        print('数据库关闭!')




# 取出数据放在字典中

def findall_data(symbol):
    # 1. 建立数据库连接
    connection = pymssql.connect(host='localhost',
                                 server='LAPTOP-',# 修改
                                 port='1433',
                                 user='sa', password='',# 修改
                                 database='NASDAQ',
                                 charset='GBK',
                                 autocommit=True)
    # 返回的数据
    if connection:
        print('数据库连接成功！')
    data=[]

    try:
        with connection.cursor() as cursor:
            if symbol == 'AAPL':
                sql = "select HDate,Open1,High,Low,Close1,Volume,Symbol from HistoricalQuote where Symbol='AAPL'"
            elif symbol == 'FUSHIDA':
                sql = "select HDate,Open1,High,Low,Close1,Volume,Symbol from HistoricalQuote where Symbol='FUSHIDA'"
            elif symbol == 'GELIDIANQI':
                sql = "select HDate,Open1,High,Low,Close1,Volume,Symbol from HistoricalQuote where Symbol='GELIDIANQI'"
            cursor.execute(sql)

            result_set=cursor.fetchall()
            for row in result_set:
                fields={}
                fields['Date']=row[0]
                fields['Open']=float(row[1])
                fields['High']=float(row[2])
                fields['Low']=float(row[3])
                fields['Close']=float(row[4])
                fields['Volume']=row[5]
                data.append(fields)

    except pymssql.DatabaseError as error:
        print('数据查询失败'+error)

    finally:
        connection.close()
        print('数据库关闭成功！')
    # data 是列表，每个元素是字典
    return data


