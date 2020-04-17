from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2

import dao.user.user as ud
import dao.application.application as ad
import dao.device.device as dd
import dao.pend.pend as pend
import dao.data.data as data

import misc

import os


APP_KEY_LEN = 8
DATA_DOWNLOAD_DIR = 'data'

server = Flask(__name__, template_folder='templates/')

@server.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        apps = ad.get_list(session['name'].encode('utf-8'))

        session.pop('appkey', None)
        # print('apps: ', apps)
        if apps[0]:
            return render_template('index.html', apps=apps[1])
        else:
            return render_template('index.html', feedback=apps[1])
    else:
        return render_template('index.html')



@server.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('signup.html', feedback=feedback)
        else:
            res = ud.create(username, password)
            if (not res[0]):
                return render_template('signup.html', feedback=res[1])
            else:
                session['name'] = username
        
                return redirect(url_for('index'))



@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('login.html', feedback=feedback)
        else:
            res = ud.get(username, password)
            if (not res[0]):
                return render_template('login.html', feedback=msg[1])
            else:
                session['name'] = username
        
                return redirect(url_for('index'))



@server.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@server.route('/new-app')
def new_application():
    if 'name' in session:
        return render_template('new-app.html')
    else:
        return redirect(url_for('index'))



@server.route('/app', methods=['GET', 'POST'])
def app():
    if 'name' in session:
        if request.method == 'GET':
            
            session['appkey'] = request.args.get('appkey')

            app = ad.get(session['appkey'])
            devs = dd.get_list(app[1][1])
        
            try:
                filelist = [f for f in os.listdir(DATA_DOWNLOAD_DIR) if f.startswith(session['appkey'])]
                for f in filelist:
                    os.remove(DATA_DOWNLOAD_DIR+'/'+f)
            except OSError:
                pass

           # print('devs : ', devs)
            return render_template('app.html', app=app[1], devs=devs[1])
        else:
            if request.form['appname'] == '':
                error = 'Application name cannot be empty.'
                return render_template('new-app.html', feedback=error)
            else:
                appkey = misc.rand_str(APP_KEY_LEN)
                res = ad.create(request.form['appname'], appkey, session['name'], request.form['appdesc'])
            
                if not res[0]:
                    return render_template('new-app.html', feedback=res[1])
            
                res = dd.create_table(appkey)
            
                if not res[0]:
                    ad.delete(appkey)
                    return render_template('new-app.html', feedback=res[1])
            
                return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@server.route('/delete-app')
def delete_app():
    if 'name' in session:
        devs = dd.get_list(session['appkey'])
    
        for dev in devs[1]:
            data.delete_table(session['appkey'], dev[1])
    
        dd.delete_table(session['appkey'])
    
        res = ad.delete(session['appkey'])
    
        if not res[0]:
            return redirect(url_for('app'))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@server.route('/add-dev')
def new_dev():
    if 'name' in session:
        dev_list = dd.get_list(session['appkey'])
    
    #print('dev list : ', dev_list)

        if not dev_list[0]:
            return render_template('add-dev.html', feedback=dev_list[1])
        else:
            return render_template('add-dev.html', free_ids=misc.prep_id_range(dev_list[1]))
    else:
        return redirect(url_for('index'))
 


@server.route('/dev', methods=['GET', 'POST'])
def dev():
    if 'name' in session:
        if request.method == 'GET':
            dev = dd.get(session['appkey'], request.args.get('id'))

            session['devid'] = dev[1][1]
            session['devname'] = dev[1][0]
        
            last = data.get_last_n(session['appkey'], session['devid'], 1)
        
            ltup = 'Device have not sent data yet'

            if last[0]:
                ltup = last[1][0][1]

            return render_template('dev.html', dev=dev[1], appkey=session['appkey'], ltup=ltup)
        else:
            res = dd.create(request.form['devname'], request.form['devid'], session['appkey'], request.form['devdesc'])

            if not res[0]:
                return render_template('add-dev.html', feedback=res[1])
            else:
                res = data.create_table(session['appkey'], request.form['devid'])
            
                if not res[0]:
                    dd.delete(session['appkey'], request.form['devid'])
                    return render_template('add-dev.html', feedback=res[1])
                else:
                    return redirect(url_for('app', appkey=session['appkey']))
    else:
        return redirect(url_for('index'))


@server.route('/dev-conf', methods=['GET', 'POST'])
def dev_conf():
    if 'name' in session and 'devid' in session:
        if request.method == 'GET':
            return render_template('dev-conf.html', devname=session['devname'])
        else:
        
            argslen = len(request.form['arg']) + 1
            args = bytearray(argslen + 2)
            args[0] = int(request.form['confid'])
            args[1] = argslen
        
            bstr = bytes(request.form['arg'])
            i = 0
            while i < argslen - 1:
                args[2+i] = bstr[i]
                i += 1

            base64_args = binascii.b2a_base64(args).decode('utf-8')

            pend.create(session['appkey'], session['devid'], base64_args)

        #print('msg = ', args)
        #print('base64 = ', base64_args)
        #print(type(request.form['arg'].encode('utf-8')))
        #print(request.form['arg'].encode('utf-8'))
        
            return redirect(url_for('dev', id=session['devid']))
    else:
        return redirect(url_for('index'))


@server.route('/delete-dev')
def delete_dev():
    if 'name' in session and 'devid' in session:
        data.delete_table(session['appkey'], session['devid'])
        res = dd.delete(session['appkey'], session['devid'])

        return redirect(url_for('app', appkey=session['appkey']))
    else:
        return redirect(utl_for('index'))


@server.route('/dev-data')
def dev_data():
    if 'name' in session and 'devid' in session:
        last = data.get_last_n(session['appkey'], session['devid'], 10)  
        count = data.get_count(session['appkey'], session['devid'])

        last_ctr = 10
        if count[1][0] < 10:
            last_ctr = count[1][0]

        #print(last)
        #print(count)
        if count[1][0] > 0:
            return render_template('dev-data.html', data=last[1], total=count[1][0], lastctr=last_ctr, devname=session['devname'])
        else:
            return render_template('dev-data.html', devname=session['devname'])
    else:
        return redirect(utl_for('index'))

@server.route('/data-csv')
def data_csv():
    if 'name' in session and 'devid' in session:
        dumpd = data.get_all(session['appkey'], session['devid'])

        fn = session['appkey']+ '_' +str(session['devid'])+ '.csv'

        with open(DATA_DOWNLOAD_DIR+'/'+fn, 'w') as f: 
            for d in dumpd[1][0][2]:
                f.write(d)
                f.write(',')
            f.write('\n')
        
            for row in dumpd[1]:
                for v in row[2]:
                    f.write(str(row[2][v]))
                    f.write(',')
                f.write('\n')
    
        return send_from_directory(DATA_DOWNLOAD_DIR, fn, as_attachment=True)
    else:
        return redirect(utl_for('index'))
        

if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


