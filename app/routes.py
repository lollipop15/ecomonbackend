from app import app
from app import db
from sqlalchemy.inspection import inspect
from flask import jsonify, request, current_app
from russian_map import russian_map
from datetime import datetime, timedelta
import jwt
from app import auth
from app.models import UserType, User, Point, Try, Measurement
import re
from werkzeug.security import generate_password_hash
import pandas as pd
from sklearn import preprocessing
from sqlalchemy import func
from fbprophet import Prophet


def get_object_by_name(object_name):
    for clazz in db.Model._decl_class_registry.values():
        try:
            if (clazz.__tablename__.lower() == object_name.lower()):
                model_object = clazz
                break
        except:
            continue
    return model_object


@app.route('/api/auth/', methods=['POST'])
def login():
    data = request.get_json()
    user = auth.authenticate(**data)

    if not user:
        return jsonify({ 'message': 'Invalid credentials', 'authenticated': False }), 401
    token = jwt.encode({
        'sub': user.Login,
        'iat':datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=600)},
        current_app.config['SECRET_KEY'])
    user_type = UserType.query.filter_by(Type_id = user.Type_id).first()
    return jsonify({ 'token': token.decode('UTF-8'), 'userType': user_type.Type_name, 'userName': user.FIO })

@app.route('/api/auth/check', methods=['GET'])
@auth.token_required
def check_token(user):
    if user:
        return jsonify({"check": True})

@app.route('/api/sign_up', methods=['POST'])
@auth.token_required
@auth.only_admin
def sign_up(user):
    req_data = request.json
    req_data['Password_hash'] = generate_password_hash(req_data['Password_hash'])
    new_user = User(**req_data)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'result': 'success'})


@app.route('/api/object/<object_name>/<int:object_id>', methods=['GET', 'PUT', 'DELETE', 'POST'])
@app.route('/api/object/<object_name>', methods=['GET', 'POST'])
@auth.token_required
@auth.check_user_rights
def object_endpoint(user, object_name, object_id = None):
    model_object = get_object_by_name(object_name)
    return model_object.get_delete_put_post(object_id)

@app.route('/api/filter/<object_name>', methods=['GET'])
@auth.token_required
@auth.check_user_rights
def filter_endpoint(user, object_name):
    model_object = get_object_by_name(object_name)
    data = request.args.to_dict()
    data_int = {}
    for key in data:
        try:
            data_int[key] = int(data[key])
        except:
            data_int[key] = data[key]
    return model_object.get_delete_put_post(prop_filters = data_int)

@app.route('/api/filter/unauth/point', methods=['GET'])
def filter_point_unauth_endpoint():
    object_name = 'point'
    model_object = get_object_by_name(object_name)
    data = request.args.to_dict()
    data_int = {}
    for key in data:
        try:
            data_int[key] = int(data[key])
        except:
            data_int[key] = data[key]
    return model_object.get_delete_put_post(prop_filters = data_int)

@app.route('/api/filter/unauth/measurement_type', methods=['GET'])
def filter_measurement_type_unauth_endpoint():
    object_name = 'measurement_type'
    model_object = get_object_by_name(object_name)
    data = request.args.to_dict()
    data_int = {}
    for key in data:
        try:
            data_int[key] = int(data[key])
        except:
            data_int[key] = data[key]
    return model_object.get_delete_put_post(prop_filters = data_int)


@app.route('/api/definition/<object_name>', methods=['GET'])
@auth.token_required
@auth.check_user_rights
def definition_endpoint(user, object_name):
    model_object = get_object_by_name(object_name)
    inst = inspect(model_object)
    result = []
    for col in inst.mapper.column_attrs:
        if ((col.key != primary_key) and (col.key in id_aliases)):
            alias_name = id_aliases[col.key]
            russian_name = russian_map[alias_name.lower()]
        else:
            alias_name = col.key
            russian_name = russian_map[col.key.lower()]
        result.append({"name": col.key, "is_primary_key": (col.key == primary_key), "russian_name": russian_name, 'alias': alias_name})
    return jsonify(result)

@app.route('/api/definition/unauth/point', methods=['GET'])
def definition_endpoint_unauth_point():
    object_name = 'point'
    model_object = get_object_by_name(object_name)
    inst = inspect(model_object)
    primary_key = inst.primary_key[0].name
    result = []
    for col in inst.mapper.column_attrs:
        if ((col.key != primary_key) and (col.key in id_aliases)):
            alias_name = id_aliases[col.key]
            russian_name = russian_map[alias_name.lower()]
        else:
            alias_name = col.key
            russian_name = russian_map[col.key.lower()]
        result.append({"name": col.key, "is_primary_key": (col.key == primary_key), "russian_name": russian_name, 'alias': alias_name})
    return jsonify(result)


@app.route('/api/objects', methods=['GET'])
@auth.token_required
def all_objectes(user):
    result = []
    user_type = UserType.query.filter_by(Type_id = user.Type_id).first()
    for clazz in db.Model._decl_class_registry.values():
        try:
            if (auth.user_rights[user_type.Type_name].count(clazz.__tablename__.lower()) != 0):
                result.append({"table_name": clazz.__tablename__.lower(), "russian_table_name": russian_map[clazz.__tablename__.lower()]})
        except:
            continue
    return jsonify(result)

@app.route('/api/extended/object/<object_name>', methods=['GET'])
@auth.token_required
@auth.check_user_rights
def extended_objects(user, object_name):
    model_object = get_object_by_name(object_name)
    inst = inspect(model_object)
    relationships = inst.relationships
    relation_tables = []
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    for relation in relationships:
        if (relation.direction.name == 'MANYTOONE'):
            for prop in relation.local_columns:
                foreign_key = str(prop).split('.')[1]
            table = pattern.sub('_', str(relation).split('.')[1])
            relation_tables.append({"table": table, "foreign_key": foreign_key})
    if (relation_tables != []):
        relation_objects = []
        for relation_table in relation_tables:
            for clazz in db.Model._decl_class_registry.values():
                try:
                    if (clazz.__tablename__.lower() == relation_table["table"].lower()):
                        relation_objects.append(clazz)
                except:
                    continue
        query = db.session.query(model_object, *relation_objects)
        for relation_object in relation_objects:
            query = query.join(relation_object)
        query = query.all()
        result_keys = []
        query_results = []
        for line in query:
            for line_object in line:
                for key in line_object.__mapper__.c.keys():
                    result_keys.append(key)
        for line in query:
            temp_line1 = {}
            temp_line2 = {}
            for line_object in line:
                temp_line1.update(line_object.__dict__)
            for key in temp_line1.keys():
                if (result_keys.count(key) != 0):
                    temp_line2[key] = temp_line1[key]
            query_results.append(temp_line2)
        return jsonify(query_results)
    else:
        return model_object.get_delete_put_post(None)

@app.route('/api/extended/object/<object_name>/relations', methods=['GET'])
@auth.token_required
@auth.check_user_rights
def extended_object_relations(user, object_name):
    model_object = get_object_by_name(object_name)
    inst = inspect(model_object)
    relationships = inst.relationships
    relation_tables = []
    for relation in relationships:
        if (relation.direction.name == 'MANYTOONE'):
            for prop in relation.local_columns:
                foreign_key = str(prop).split('.')[1]
            table = pattern.sub('_', str(relation).split('.')[1])
            relation_tables.append({"table": table, "foreign_key": foreign_key})
    if (relation_tables != []):
        relation_objects = {}
        for relation_table in relation_tables:
            for clazz in db.Model._decl_class_registry.values():
                try:
                    if (clazz.__tablename__.lower() == relation_table["table"].lower()):
                        relation_objects[relation_table["foreign_key"]] = clazz.get_delete_put_post(None).json
                except:
                    continue
        return jsonify(relation_objects)
    else:
        return jsonify({})

@app.route('/api/extended/object/unauth/point/relations', methods=['GET'])
def extended_object_relations_unauth_point():
    object_name = 'point'
    model_object = get_object_by_name(object_name)
    inst = inspect(model_object)
    relationships = inst.relationships
    relation_tables = []
    for relation in relationships:
        if (relation.direction.name == 'MANYTOONE'):
            for prop in relation.local_columns:
                foreign_key = str(prop).split('.')[1]
            table = pattern.sub('_', str(relation).split('.')[1])
            relation_tables.append({"table": table, "foreign_key": foreign_key})
    if (relation_tables != []):
        relation_objects = {}
        for relation_table in relation_tables:
            for clazz in db.Model._decl_class_registry.values():
                try:
                    if (clazz.__tablename__.lower() == relation_table["table"].lower()):
                        relation_objects[relation_table["foreign_key"]] = clazz.get_delete_put_post(None).json
                except:
                    continue
        return jsonify(relation_objects)
    else:
        return jsonify({})

@app.route('/api/extended/object/try', methods = ['POST'])
@auth.token_required
def post_try_with_measurement(user):
    data = request.get_json()
    data['try']['Start_time'] = datetime(int(data['try']['Start_time'].split('-')[0]), int(data['try']['Start_time'].split('-')[1]), int(data['try']['Start_time'].split('-')[2]), data['try']['hour'], data['try']['minutes'], 0)
    data['try'].pop('hour')
    data['try'].pop('minutes')
    data['try']['User_ID'] = user.User_ID
    if (data['try']['Is_public']):
        data['try']['Is_public'] = 1
    else:
        data['try']['Is_public'] = 0
    newTry = Try(**data['try'])
    db.session.add(newTry)
    db.session.commit()
    for measurement in data['measurements']:
        newMeasurement = Measurement(Try_ID = newTry.Try_ID, **measurement)
        db.session.add(newMeasurement)
    db.session.commit()
    return jsonify({})

@app.route('/api/statistic/point/<int:point_id>/measurement_type/<int:measurement_type_id>', methods = ['GET'])
def get_point_statistic(point_id, measurement_type_id):
    data = request.args.to_dict()
    freq = 'H'
    if ((datetime.strptime(data['toDate'], '%Y-%m-%d')-datetime.strptime(data['fromDate'], '%Y-%m-%d')).days > 14):
        freq = 'D'
    query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).filter(Try.Start_time >= data['fromDate']).filter(Try.Start_time <= data['toDate']).order_by(Try.Start_time)
    df = pd.read_sql(query.statement, db.session.bind)
    df = df.set_index('Start_time').groupby(pd.Grouper(freq=freq)).mean()
    df = df.dropna()
    result = []
    for index, line in df.iterrows():
        result.append({'x': index, 'y': line['Value']})
    return jsonify(result)

@app.route('/api/statistic/point/<int:point_id>/measurement_type/<int:measurement_type_id>/normalize', methods = ['GET'])
def get_normalize_point_statistic(point_id, measurement_type_id):
    query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).order_by(Try.Start_time).all()
    result = []
    dataToNormalize = {'y': []}
    for line in query:
        result.append({'x': line[1].Start_time, 'y': line[0].Value})
        dataToNormalize['y'].append(line[0].Value)
    df = pd.DataFrame(dataToNormalize)
    y = df[['y']].values.astype(float)
    min_max_scaler = preprocessing.MinMaxScaler()
    y_scaled = min_max_scaler.fit_transform(y)
    df_norm = pd.DataFrame(y_scaled)
    for index, row in df_norm.iterrows():
        result[index]['y'] = row[0]
    return jsonify(result)

@app.route('/api/statistic/normalize', methods = ['POST'])
def get_normalize_points_statistic():
    req_data = request.get_json()
    full_result = []
    for data in req_data:
        freq = 'H'
        if ((datetime.strptime(data['toDate'], '%Y-%m-%d')-datetime.strptime(data['fromDate'], '%Y-%m-%d')).days > 14):
            freq = 'D'
        point_id = data['point']
        measurement_type_id = data['meas']
        query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).filter(Try.Start_time >= data['fromDate']).filter(Try.Start_time <= data['toDate']).order_by(Try.Start_time)
        df = pd.read_sql(query.statement, db.session.bind)
        df = df.set_index('Start_time').groupby(pd.Grouper(freq=freq)).mean()
        df = df.dropna()
        result = []
        dataToNormalize = {'y': []}
        for index, line in df.iterrows():
            result.append({'x': index, 'y': line['Value']})
            dataToNormalize['y'].append(line['Value'])
        y = df[['y']].values.astype(float)
        min_max_scaler = preprocessing.MinMaxScaler()
        y_scaled = min_max_scaler.fit_transform(y)
        df_norm = pd.DataFrame(y_scaled)
        for index, row in df_norm.iterrows():
            result[index]['y'] = row[0]
        full_result.append(result)
    return jsonify(full_result)

@app.route('/api/statistic/correlation', methods = ['POST'])
def get_correlation_points_statistic():
    req_data = request.get_json()
    dataToCor = {}
    for data in req_data:
        point_id = data['point']
        measurement_type_id = data['meas']
        query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).filter(Try.Start_time >= data['fromDate']).filter(Try.Start_time <= data['toDate']).order_by(Try.Start_time).all()
        element_name = str(data['point'])+'_'+str(data['meas'])
        dataToCor[element_name] = []
        for line in query:
            dataToCor[element_name].append(float(line[0].Value))
    df = pd.DataFrame(dataToCor)
    df_corr = df.corr(method = 'spearman')
    result = []
    for index, row in df_corr.iterrows():
        result.append(row[str(req_data[0]['point'])+'_'+str(req_data[0]['meas'])])
    return jsonify(result)


@app.route('/api/forecast', methods = ['POST'])
def get_forecast():
    req_data = request.get_json()
    full_uni_data = []
    result = []
    predict_add = []
    freq = 'H'
    if ((datetime.strptime(req_data[0]['toDate'], '%Y-%m-%d')-datetime.strptime(req_data[0]['fromDate'], '%Y-%m-%d')).days > 14):
        freq = 'D'
    point_id = req_data[0]['point']
    measurement_type_id = req_data[0]['meas']
    query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).filter(Try.Start_time >= req_data[0]['fromDate']).filter(Try.Start_time <= req_data[0]['toDate']).order_by(Try.Start_time)
    df = pd.read_sql(query.statement, db.session.bind)
    df = df.set_index('Start_time').groupby(pd.Grouper(freq=freq)).mean()
    df = df.dropna()
    simple_result = []
    for index, line in df.iterrows():
        simple_result.append({'x': index, 'y': line['Value']})
    full_req_result = []
    full_req_result.append(simple_result)
    period = int((datetime.strptime(req_data[0]['toDate'], '%Y-%m-%d')-datetime.strptime(req_data[0]['fromDate'], '%Y-%m-%d')).days * 0.2 * 24)
    for data in req_data:
        freq = 'H'
        #if ((datetime.strptime(data['toDate'], '%Y-%m-%d')-datetime.strptime(data['fromDate'], '%Y-%m-%d')).days > 14):
        #    freq = 'D'
        point_id = data['point']
        measurement_type_id = data['meas']
        query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).filter(Try.Start_time >= data['fromDate']).filter(Try.Start_time <= data['toDate']).order_by(Try.Start_time)
        df = pd.read_sql(query.statement, db.session.bind)
        df = df.set_index('Start_time').groupby(pd.Grouper(freq=freq)).mean()
        df = df.dropna()
        uni_data = pd.DataFrame()
        uni_data['y'] = df['Value'].values 
        uni_data['ds'] = df.index
        full_uni_data.append(uni_data)
    if (len(full_uni_data) == 1):
        m = Prophet(changepoint_prior_scale=0.01).fit(full_uni_data[0])
        fcst = m.predict(future)
        result_df = fcst[['ds', 'yhat']]
    else:
        uni = full_uni_data[0]
        m = Prophet(changepoint_prior_scale=0.01).fit(full_uni_data[1])
        future = m.make_future_dataframe(periods=period, freq='H')
        fcst = m.predict(future)
        uni_fore = fcst[['ds', 'yhat']]
        i = 2
        m_r = Prophet(changepoint_prior_scale=0.01)
        m_r.add_regressor('add' + str(1))
        while i < len(full_uni_data):
            m = Prophet(changepoint_prior_scale=0.01).fit(full_uni_data[i])
            future = m.make_future_dataframe(periods=period, freq='H')
            fcst = m.predict(future)
            temp_df = fcst[['ds', 'yhat']]
            temp_df = temp_df.rename(columns = {'ds': 'ds', 'yhat': 'add' + str(i)})
            uni_fore = pd.concat([uni_fore, temp_df['add' + str(i)]], axis=1)
            m_r.add_regressor('add' + str(i))
            i = i + 1
        uni_fore = pd.concat([uni_fore, uni['y']], axis = 1)
        df_train = uni_fore.head(len(uni_fore) - period)
        df_test = uni_fore.tail(period)
        m_r.fit(df_train)
        fcst = m_r.predict(uni_fore.drop(columns="y"))
        result_df = fcst[['ds', 'yhat']]
    if ((datetime.strptime(req_data[0]['toDate'], '%Y-%m-%d')-datetime.strptime(req_data[0]['fromDate'], '%Y-%m-%d')).days > 14):
        freq = 'D'
        result_df = result_df.set_index('ds').groupby(pd.Grouper(freq=freq)).mean()
        result_df.dropna()
        for index, line in result_df.iterrows():
            result.append({'x': index, 'y': line['yhat']})
        full_req_result.append(result)
        return jsonify(full_req_result)
    for index, line in result_df.iterrows():
        result.append({'x': line['ds'], 'y': line['yhat']})
    full_req_result.append(result)
    return jsonify(full_req_result)


@app.route('/api/statistic/periods', methods = ['POST'])
def get_periods_points_statistic():
    req_data = request.get_json()
    full_result = []
    for data in req_data:
        point_id = data['point']
        measurement_type_id = data['meas']
        query = db.session.query(Measurement, Try).join(Try).filter(Measurement.Point_ID == point_id, Measurement.Measurement_type_ID == measurement_type_id).order_by(Try.Start_time)
        df = pd.read_sql(query.statement, db.session.bind)
        full_result.append({'min': df['Start_time'].min(), 'max': df['Start_time'].max()})
    return jsonify(full_result)
