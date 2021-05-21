
# Import necessary modules
import os
from decouple import config
from flask_pymongo import PyMongo
from flask import Flask, request, render_template, json, redirect, url_for
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# import Handlers

app = Flask(__name__)

app.config["MONGO_URI"] = config('MONGO_URI_LANDSCAPE')
mongo = PyMongo(app)

lib   = mongo.db.dev_library
book  = mongo.db['library'] 
library = mongo.db['new']
feed = mongo.db['feedback']

df=pd.read_csv('month.csv')

one_plot = ""
compare_variable=""
year_one = "2015"

# Main route

@app.route('/', methods=['GET'])
def index():

    response = get_all_libraries_wrt_parent_api()
    result   = response['result']
    # return render_template('index.html')
    return render_template('home_landscape.html', result = result)

# To show Modal

@app.route('/showmodal')
def show_modal():

    libname= request.args.get('lib', None)

    response = get_all_libraries_wrt_parent_api()
    result   = response['result'] 
    image, domain = get_logo(libname)

    print("?????"+libname)
    #return render_template('index.html')   
    return render_template('home_landscape_modal.html', result= result, name= libname, logo= image, domain= domain)

# Function to get Technology, Domain, Logo

@app.route("/api/get/libraries/parent", methods = ['GET'])
def get_all_libraries_wrt_parent_api():

    result = []

    # parent_lib = 'Frontend'
    parent_lib= lib.distinct('Interface')

    for parent in parent_lib:
        
        libraries_under_parent = lib.find({'Interface' : parent})

        lib_list  = []

        for item in libraries_under_parent:
            library_obj = {
                "library_name" : item['Technology'],
                "logo"         : item['Image_Link'],
                "domain"       : item['Interface']
            }
            lib_list.append(library_obj)

        result.append({
            "parent_library" : parent,
            "libraries"      : lib_list,
            "count"          : len(lib_list)
        })

    result_dict = {
        "result": result
    }

    return result_dict

# Get logo, name

@app.route("/logo_get/<libname>", methods = ['GET'])
def get_logo(libname):
    
    parent = libname
        
    libraries_under_parent = lib.find({'Technology' : parent})

    for item in libraries_under_parent:

        logo = item['Image_Link']
        domain = item['Interface']
        
    return logo, domain
    
# Get Profile page

@app.route("/profile-landing",methods=["POST","GET"])
def get_profile():

    global domain, name
    name   = request.form['name']
    domain = request.form['domain']
    print(name)
    return redirect(url_for("get_tech_profile"))

# Redirect to Contact form

@app.route("/getcontactform",methods=["POST","GET"])
def getcontactform():

    message = ""

    return render_template("contact.html",msg = message)

# Contact Form

@app.route("/contactform",methods=["POST","GET"])
def contactform():

    doc = ""
    message = ""

    tech   = request.form['tech']
    mail  = request.form['email']
    note   = request.form['note'] 

    suggestion = {
        "email": mail,
        "technology": tech,
        "suggestion": note
    }

    doc = feed.insert_one(suggestion)

    if doc :
        message = "Your Response was submitted successfully. We will reach you within 1 week."
        print(message)
    
    return render_template("contact.html",msg = message)


@app.route("/dedicated-profile",methods = ['POST','GET'])
def get_tech_profile():

    global domain, name
    name   = name.lower()
    domain = domain

    contacts = book.find({"Technology": name})
    contact_list = []

    for item in contacts:
        contact_obj = {
            "git_repo_link"         : item['git_repo_link'],
            "git_commit_count"      : item['git_commit_count'],
            "git_fork_count"        : item['git_fork_count'],
            "git_watcher_count"     : item['git_watcher_count'],
            "git_subscriber_count"  : item['git_subscriber_count'],
            "Technology"            : item['Technology'],
            "Interface"             : item['Interface'],
            "Image_link"            : item['Image_link'],
            "writtenin"             : item['Writtenin'],
            "About"                 : item['About'],
            "Source"                : item['Source'] 
            
        }
        contact_list.append(contact_obj)

    result_dict = {
        "Contacts" : contact_list
    }
     
    return render_template("profile.html",rows = contact_list)


@app.route("/table-data" , methods = ["POST","GET"])
def table_data():

    global year_one, name, domain
    print(year_one)

    contacts_year = library.distinct('year')

    year_list = []
    year_obj = {}
    
    for item in contacts_year :
        year_obj = {
        'year' : item 
        }
        year_list.append(year_obj)
    
    f_year = year_one

    if request.method == "POST":
   
        f_year = request.form["Year"]

    table_variable      = name.lower()
    domain_name         = domain

    contacts = library.find({ 'year' : f_year })
    contact_list = []
    contact_obj = {}

    for item in contacts:
        # u_confirmed = item['values']
        contact_obj = {
              
            "year"        : item['year'],  
            "month"       : item['month'],
            "values"      : item[table_variable]
            
        }

        contact_list.append(contact_obj)
        
    return render_template('tables.html', rows_data = contact_list ,tech = table_variable, column = year_list , domain = domain_name)

# Past dataset { till 2017 }

@app.route("/initial-data" , methods = ["POST","GET"])
def initial_data():

    Interface_variable      = domain
    original_graph_variable = name.lower()
    print(domain)
    x_value =   df['month']
    y_value =   df[original_graph_variable][:108]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = x_value, y = y_value,
                        mode = 'lines+markers',
                        name = 'lines'))
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(title_text = 'month')
    fig.update_yaxes(title_text = original_graph_variable)
    fig.update_layout(title_text = original_graph_variable +" "+ 'Visualization')
    scatter_one = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

    contacts = book.find({"Interface":Interface_variable})
    contact_list = []
    contact_obj = {}

    for item in contacts :
        if item['Technology'] != original_graph_variable :
            contact_obj = {
                "Technology"  : item['Technology']   
            }

            contact_list.append(contact_obj)
            
    print(contact_list)
        
    return render_template('original_graph.html', plot1 = scatter_one , v = contact_list)

# Forecast data { from 2018 onwards }

@app.route("/forecast-data" , methods = ["POST","GET"])
def forecast_data():

    global domain
    Interface_variable      = domain
    forecast_graph_variable = name.lower()
    forecast_variable       = forecast_graph_variable + '_forecast'
    print(domain)

    x_value =   df['month']
    y_past  =   df[forecast_variable][:108]
    y_value =   df[forecast_variable][108:168]
    print(df[forecast_variable][108])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x = x_value, y= y_past,
                    mode='lines+markers',
                    line=dict(color="#0000ff"),
                    name='past data'))
    fig.add_trace(go.Scatter(x = x_value[108:168], y = y_value,
                    mode='lines+markers',
                    line=dict(color="#ff0000"),
                    name='forecast data'))
    fig.update_xaxes(type = 'category')
    fig.update_xaxes(title_text = 'month')
    fig.update_yaxes(title_text = forecast_graph_variable)
    fig.update_layout(title_text = forecast_graph_variable +" "+ 'Visualization')
    scatter_one = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

    contacts = book.find({"Interface" : Interface_variable})
    contact_list = []
    contact_obj = {}

    for item in contacts:
        if item['Technology']!= forecast_graph_variable :

            contact_obj = {
                "Technology"  : item['Technology']+ '_forecast'    
            }

            contact_list.append(contact_obj)
        
    return render_template('forecast_graph.html', plot1 = scatter_one , v = contact_list)


@app.route("/full-data",methods=["POST","GET"])
def full_data():
    
    full_graph_variable = domain

    x_value = df['month']

    contacts = book.find({"Interface" : full_graph_variable})
    contact_list = []
    contact_obj = {}

    fig = go.Figure()
    for item in contacts:
        Technology = item['Technology'] + '_forecast'   
        fig.add_trace(go.Scatter(x=x_value, y=df[Technology],
                        mode='lines',
                        name=Technology))

    fig.update_xaxes(type='category')
    fig.update_xaxes(title_text='month')
    fig.update_yaxes(title_text='data')
    
    scatter_one = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('compare_graph.html', plot1 = scatter_one)


@app.route("/compare-data-past",methods=["POST","GET"])
def compare_data_past():
    
    compare_graph_variable = name.lower()

    x_value = df['month'][:108]
    y_value = df[compare_graph_variable][:108]
    y1_value = compare_variable
    y2_value = df[y1_value][:108]
    print(y2_value)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_value, y=y_value,
                        mode='lines',
                        name=compare_graph_variable))
    fig.add_trace(go.Scatter(x=x_value, y=y2_value,
                        mode='lines',
                        name=y1_value))
    fig.update_xaxes(type='category')
    fig.update_xaxes(title_text='month')
    fig.update_yaxes(title_text='data')
    
    scatter_one = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('compare_graph.html', plot1 = scatter_one)
    
@app.route("/compare-data-future",methods=["POST","GET"])
def compare_data_future():
    
    compare_graph_variable = name.lower()+ '_forecast'

    x_value = df['month'][108:168]
    y_value = df[compare_graph_variable][108:168]
    y1_value = compare_variable
    y2_value = df[y1_value][108:168]
    print(y2_value)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_value, y=y_value,
                        mode='lines',
                        name=compare_graph_variable))
    fig.add_trace(go.Scatter(x=x_value, y=y2_value,
                        mode='lines',
                        name=y1_value))
    fig.update_xaxes(type='category')
    fig.update_xaxes(title_text='month')
    fig.update_yaxes(title_text='data')
    
    scatter_one = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('compare_graph.html', plot1 = scatter_one)
    

@app.route("/compare-past-variable/<v>",methods=["POST","GET"])
def compare_past_variable(v):

    global compare_variable
    compare_variable = v
    return redirect(url_for("compare_data_past"))


@app.route("/compare-future-variable/<v>",methods=["POST","GET"])
def compare_future_variable(v):

    global compare_variable
    compare_variable = v
    return redirect(url_for("compare_data_future"))

@app.route("/vary-year/<v>",methods=["POST","GET"])
def vary_year(v):

    global year_one
    year_one = v
    return redirect(url_for("table_data"))


if __name__ == "__main__":

    global domain, name
    app.run('127.0.0.1', 5000, True)
