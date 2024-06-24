from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
import json
from django.views.decorators.csrf import csrf_exempt
import pymysql,random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime,timedelta
from django.urls import reverse
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

import pymongo
from bson import ObjectId
from bson.decimal128 import Decimal128


def dbconnection():

    try:
        mongodb_uri = 'mongodb+srv://booleanbraintechnologies:UQLCbpSzxEYqxFK1@bbt0012024.zv8b9cf.mongodb.net/'
        db_name = 'bysani' 
        client = pymongo.MongoClient(mongodb_uri)
        db = client[db_name]
        print("Connection Success to database::", db.name)
        return db
    except:
        print("Connection Error")
        return db


def login_page(request):     
    return render(request,'login_page.html')

def index(request):
    user_id = request.GET.get('user_id')
    print('userID::::', user_id)
    return render(request, 'index.html', {'user_id': user_id})

def logout_page(request):
    return render(request,'login_page.html')

def road_info(request, road_type):
    template_name = f"road_{road_type}.html"
    return render(request, template_name)

  
def road_sec_info(request, road_type):
    template_name = f"{road_type}"
    return render(request, template_name)

def generateReport(request):
    return render(request, 'generate_pdf.html')


def generate_random_passwords():
    first_digit = random.choice('123456789')  # Ensure the first digit is not 0
    remaining_digits = ''.join(random.choices('0123456789', k=5))  # Generate the remaining 5 digits
    password = first_digit + remaining_digits
    return password



def send_email(username, email, phone_number):
    try:
        db = dbconnection()  # Establish MongoDB connection
        collection = db['user_details']

        # Check if user exists in MongoDB
        user = collection.find_one({"Email": email})
        
        if not user:
            print('User does not exist, adding details to database')

            # Prepare document to insert into MongoDB
            user_document = {
                "FullName": username,
                "Email": email,
                "Phone_Number": phone_number,
                "verified": False  # Assuming new users are not verified initially
            }

            # Insert document into MongoDB collection
            result = collection.insert_one(user_document)

            # Get the ID of the newly inserted document
            user_id = result.inserted_id

            # Send OTP for registration
            otp = generate_random_passwords()
            send_otp_email(email, otp, user_id)
            print('OTP sent for registration')

            return True, str(user_id)

        else:
            user_id = user['_id']
            verified = user.get('verified', False)

            if not verified:
                print('User exists but not verified, sending OTP to register')
                # Send OTP for registration
                otp = generate_random_passwords()
                send_otp_email(email, otp, user_id)
                print('OTP sent for verification')
            else:
                print('User exists and verified, sending OTP to sign in')
                # Send OTP for sign in
                otp = generate_random_passwords()
                send_otp_email(email, otp, user_id)
                print('OTP sent for Signing In')

            return True, str(user_id)

    except Exception as e:
        print(f"Database Error: {e}")
        return False, None
    
    # finally:
    #     if db:
    #         db.close() 

def send_otp_email(email, otp, user_id):
    print(otp, email, user_id)

    smtp_server = "smtp.mail.us-east-1.awsapps.com"
    smtp_port = 465
    smtp_password = "Rajesh2098@"
    from_email = "rajesh@booleanbraintechnologies.com"
    to_email = email
    message = MIMEMultipart("alternative")
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = 'Your OTP'
    body = f'Hello, your OTP is: {otp}'
    message.attach(MIMEText(body, 'plain'))
    
    try:
        smtp_connection = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # smtp_connection.starttls()
        smtp_connection.login(from_email, smtp_password)
        smtp_connection.sendmail(from_email, to_email, message.as_string())
        smtp_connection.quit()

        print(f"Email sent successfully to {to_email}")
        db = dbconnection()
        collection = db['otp_details']

        # Calculate expiry time (current time + 5 minutes)
        current_time = datetime.now()
        expiry_time = current_time + timedelta(minutes=5)

        # Prepare document to insert into MongoDB
        otp_document = {
            "userid": user_id,
            "otp": otp,
            "expiry_time": expiry_time
        }

        # Insert document into MongoDB collection
        result = collection.insert_one(otp_document)

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
    # finally:
    #     if db:
    #         db.close()



@csrf_exempt
def register_page(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            # print('*******',data)
            username = data['username']
            email = data['email']
            phone_number = data['phone']
            # print('...........',username, email, phone_number)
            mail_sent = send_email(username, email, phone_number)
            print('>>>>>>>',mail_sent)
            if mail_sent[0]:
                return JsonResponse({"status": "success", "redirect_url": "templates/verify_otp.html", "user_id": mail_sent[1]})
            else:
                return JsonResponse({"status": "error", "message": "Error in sending email"}, status=500)

        except Exception as e:
            print(f"Error in registering: {e}")
            return JsonResponse({"status": "error", "message": f"Error in registering: {e}"}, status=500)
    else:
        return render(request, 'login_page.html')
    

def signin_page(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        print("email...................", email)
        try:
            db = dbconnection()
            details = db['user_details']
            result = details.find_one({"Email": email, "verified": True}, {"_id": 1, "Email": 1})
            if result is not None:
                user_id = result['_id']
                otp = generate_random_passwords()
                send_otp_email(email, otp, user_id)
                print("Mail sent successfully.")
                
                # Assuming you are using Flask, return a JSON response
                return JsonResponse({"status": "success", "redirect_url": "templates/verify_otp.html", "user_id": str(user_id)})
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Email not registered. Please do register.'})
            
        except Exception as e:
            print(f"Database Error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Database Error. Please try again later.'}, status=500)
        # finally:
        #     if db:
        #         db.close()
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@csrf_exempt
def verify_otp_view(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        user_id = request.POST.get('user_id')
        print(otp)
        print(user_id)
        try:
           db = dbconnection()  # Establish MongoDB connection
           otp_collection = db['otp_details']
           user_collection = db['user_details']
           user_id = ObjectId(user_id)
           # Query OTP details from MongoDB
           otp_document = otp_collection.find_one({"otp": otp, "userid": user_id})

           if otp_document:
               expiry_time = otp_document['expiry_time']
               current_time = datetime.now()

               if expiry_time > current_time:
                   print("OTP is still valid")
                #    user_id = ObjectId(user_id)
                   # Update user_details collection to mark user as verified
                   user_collection.update_one(
                       {"_id": user_id},
                       {"$set": {"verified": True}}
                   )

                   print("User Registered")
                   url = f"{reverse('index')}?user_id={str(user_id)}" 
                   return JsonResponse({'status': 'success', 'redirect_url': url})
               else:
                   print("OTP has expired")
                   return JsonResponse({'status': 'error', 'message': 'OTP is expired'})
           else:
               print("Incorrect OTP")
               return JsonResponse({'status': 'error', 'message': 'OTP incorrect, Try again !!'})
        except Exception as e:
            print(str(e))
            return JsonResponse({'status': 'error', 'message': 'Database Error. Please try again later.'}, status=500)
        # finally:
        #     connection.close()
    else:
        return render(request, 'verify_otp.html')

    
def vcr_plot(data):
    composition = []
    for entry in data:
        vcr_str = entry['vcValues']
        vcr = eval(vcr_str)
        route_str = entry['route']
        route = eval(route_str)
        
        # Map vehicleComposition values to vehicles list
        mapped_values = [[route[index], value] for index, value in enumerate(vcr)]
        
        # Include day and session from data
        day = entry['sessionDay']
        session = entry['session']
        
        # Append mapped_vehicles along with day and session to composition list
        composition.append({'day': day, 'session': session, 'values': mapped_values})

    # Prepare the data for plotting
    sessions = []
    a_values = []
    b_values = []
    c_values = []
    d_values = []
    e_values = []

    for entry in composition:
        session_day = f"{entry['session']} - {entry['day']}"
        sessions.append(session_day)
        for value in entry['values']:
            if value[0] == 'A':
                a_values.append(value[1])
            elif value[0] == 'B':
                b_values.append(value[1])
            elif value[0] == 'C':
                c_values.append(value[1])
            elif value[0] == 'D':
                d_values.append(value[1])
            elif value[0] == 'E':
                e_values.append(value[1])

    # Create the plot
    fig = go.Figure()

    fig.add_trace(go.Bar(x=sessions, y=a_values, name='A'))
    fig.add_trace(go.Bar(x=sessions, y=b_values, name='B'))
    fig.add_trace(go.Bar(x=sessions, y=c_values, name='C'))
    fig.add_trace(go.Bar(x=sessions, y=d_values, name='D'))
    fig.add_trace(go.Bar(x=sessions, y=e_values, name='E'))

    # Update layout
    fig.update_layout(
        # title='VC Ratio by Session - Day',
        height=500,
        width = 900,
        xaxis_title='Session - Day',
        yaxis_title='V/C Ratio',
        xaxis_tickangle=-45,
        legend_title='Routes',
        template='plotly'
    )

    # Convert the plotly figure to HTML
    graph_html = pio.to_html(fig, full_html=False)

    return graph_html  


def vc_plot(data):
    db = dbconnection()
    
    collection = db['puc_values'] 

    # Perform query to get vehicles
    details = collection.find({}, {"vehicle": 1, "_id": 0})  # Projection to include only 'vehicle' field

    # Extract vehicles from cursor results
    vehicles = [doc['vehicle'] for doc in details]
    
    composition = []
    for entry in data:
        vehicle_composition_str = entry['vehicleComposition']
        vehicle_composition = eval(vehicle_composition_str)
        
        # Map vehicleComposition values to vehicles list
        mapped_vehicles = [[vehicles[index], value] for index, value in enumerate(vehicle_composition)]
        
        # Include day and session from data
        day = entry['sessionDay']
        session = entry['session']
        
        # Append mapped_vehicles along with day and session to composition list
        composition.append({'day': day, 'session': session, 'vehicles': mapped_vehicles})

    # Plotting
    fig = go.Figure()
    sessions = sorted(set(entry['session'] for entry in data))
    all_stacked_values = {vehicle: [0] * len(data) for vehicle in vehicles}
    # print(len(vehicles))
    # colors = px.colors.qualitative.Plotly[:len(vehicles)+2]
    colors = ['#33FFE3', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52', '#33FF57']
    # Initialize a dictionary to keep track of vehicles already added to the legend
    added_to_legend = {}
    # Iterate over each session
    for session in sessions:
        # print(session)
        session_data = [entry for entry in composition if entry['session'] == session]
        days = [entry['day'] for entry in session_data]
        vehicles_data = [entry['vehicles'] for entry in session_data]

        for i, (day, vehicle_data) in enumerate(zip(days, vehicles_data)):
            start_index = len(days) * sessions.index(session)
            for vehicle, value in vehicle_data:
                # Update the cumulative values for the vehicle
                all_stacked_values[vehicle][start_index + i] += value
                showlegend = vehicle not in added_to_legend
                fig.add_trace(go.Bar(
                    x=[f'{session} - {day}'],
                    y=[all_stacked_values[vehicle][start_index + i]],
                    name=vehicle,
                    marker_color=colors[vehicles.index(vehicle) % len(colors)],
                    showlegend=showlegend,
                ))
                
                if showlegend:
                    added_to_legend[vehicle] = True
    # Update the layout
    fig.update_layout(
        height=500,
        width = 900,
        xaxis_title='Session - Day',
        yaxis_title='Vehicle Count',
        barmode='stack',
        legend_title='Vehicle Names'
    )
 
    # Convert the Plotly figure to HTML
    graph_html = pio.to_html(fig, full_html=False)

    return graph_html

def intersection_list(request):
    
    db = dbconnection()
    user_id = ObjectId(request.GET.get('user_id'))
    try:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$lookup": {
                "from": "location_info",
                "localField": "location_id",  # Field in the 'results' collection
                "foreignField": "_id",        # Field in the 'location_info' collection
                "as": "location"
            }},
            {"$unwind": "$location"},
            {"$project": {
                "_id": 0,
                "value": {"$toString": "$location._id"},  # Convert ObjectId to string if needed
                "text": "$location.intersectionName"
            }},
            {"$sort": {"value": 1}}
        ]

        # results = db.results.aggregate(pipeline)
        locations = db.results.aggregate(pipeline)
        # print(locations)
        dropdown_data = [{'value': str(doc['value']), 'text': doc['text']} for doc in locations]
        # print(dropdown_data)
        return JsonResponse({'dropdown_data': dropdown_data})
    except Exception as e:
            print(str(e))
            return HttpResponse("An error occurred while fetching data.")
    # finally:
    #     db.close()
    # return render(request, 'generate_pdf.html') 

def get_result(data):
    # print(data[0])
    parsed_data = []
    for entry in data:
        vc_values = eval(entry['vcValues'])
        routes = eval(entry['route'])
        for i, route in enumerate(routes):
            parsed_data.append({
                'route': route,
                'vc_value': vc_values[i],
                'sessionDate': entry['sessionDate'],
                'sessionDay': entry['sessionDay'],
                'session': entry['session']
            })

    # Initializing max and min values
    overall_max = {'vc_value': float('-inf')}
    overall_min = {'vc_value': float('inf')}

    for entry in parsed_data:
        vc_value = entry['vc_value']
        
        if vc_value > overall_max['vc_value']:
            overall_max = entry
        
        if vc_value < overall_min['vc_value']:
            overall_min = entry

    # Printing the results
    # print("Route with the highest value:")
    # print(f"Route: {overall_max['route']}, Value: {overall_max['vc_value']}, Date: {overall_max['sessionDate']}, Day: {overall_max['sessionDay']}, Session: {overall_max['session']}")

    # print("\nRoute with the lowest value:")
    # print(f"Route: {overall_min['route']}, Value: {overall_min['vc_value']}, Date: {overall_min['sessionDate']}, Day: {overall_min['sessionDay']}, Session: {overall_min['session']}")

    result = f''' The most busiest road is {overall_max['route']} on {overall_max['sessionDay']}, {overall_max['session']} with PCU value of {overall_max['vc_value']}.
                  The least busiest road is {overall_min['route']} on {overall_min['sessionDay']}, {overall_min['session']} with PCU value of {overall_min['vc_value']}'''
    return result

def generate_pdf(request):
    # print(request.POST)
    if request.method == 'POST':
        from_date = request.POST.get('From_Date') 
        # print("fefewfrwe",from_date)
        to_date = request.POST.get('To_Date') 
        # print("jhgfh",to_date)
        if from_date and to_date:
            Intersection_Name = request.POST.get('Intersection_Name')
            # from_date = from_date +'00:00:00'
            # to_date = to_date +'23:59:59'
            db = dbconnection()
            location_id = ObjectId(Intersection_Name)
            # print(location_id)
            user_id = request.POST.get('user_id')
            # data_list = []
            try:
                pipeline = [
                    {"$match": {
                        "sessionDate": {"$gte": from_date, "$lte": to_date},
                        "user_id": ObjectId(user_id),
                        "location_id": location_id
                    }},
                    {"$lookup": {
                        "from": "location_info",
                        "localField": "location_id",
                        "foreignField": "_id",
                        "as": "location"
                    }},
                    {"$unwind": "$location"},
                    {"$project": {
                        "_id": 0,
                        "vcValues": "$vcValues",
                        "route": "$route",
                        "intersectionName": "$location.intersectionName",
                        "sessionDate": "$sessionDate",
                        "sessionDay": "$sessionDay",
                        "session": "$session",
                        "sessionTime": "$sessionTime",
                        "intersectionType": "$location.intersectionType",
                        "vehicleComposition": "$vehicle_composition"
                    }}
                ]

                data_list = list(db.results.aggregate(pipeline))
                # print(data_list)
                if len(data_list) < 1:
                    return HttpResponse("No entries in specific dates")
                result = get_result(data_list)
            except Exception as e:
                print('ERROR:::',str(e))
                return HttpResponse("An error occurred while fetching data. go back")
            
            # finally:
            #     db.close()
                
            graph_html = vcr_plot(data_list)
            graph_html_1 = vc_plot(data_list)
            context = {
                'road_info': data_list,
                'graph': graph_html,
                'graph1': graph_html_1,
                'selected_intersection': str(location_id),
                'from_date': from_date,
                'to_date': to_date,
                'user_id': str(user_id),
                'result' : result
            }
            return render(request, 'generate_pdf.html', context)
        else:
            return HttpResponse("Enter dates to generate report.")
    return render(request, 'generate_pdf.html') 


def get_puc_values(data):
    try:
        db = dbconnection()
        collection = db["puc_values"]  # Replace with your MongoDB collection name
        query = {}
        projection = {"vehicle": 1, "_id": 0}  # Default projection
        if data['ube'][0] == 'Yes':
            projection["urban_express"] = 1
        elif any(value in ['3', '4', '5'] for value in data['vol']):
            projection["divided"] = 1
        elif 'TWO' in data['obs']:
            projection["bidirectional"] = 1
        cursor = collection.find(query, projection)
        puc_values = list(cursor)
        return puc_values
    except Exception as e:
        print(f"Error fetching puc values: {e}")
    # finally:
    #     if db:
    #         db.close()  # Close MongoDB connection if open

def get_volume_values():
    try:
        db = dbconnection()  # Establish MongoDB connection
        volume_collection = db['volume_values']  # Adjust collection name as per your MongoDB setup
        # Perform find operation
        volume_values = list(volume_collection.find({}, {"_id": 0, "id": 1, "Volume": 1}))  # Example projection
        return volume_values
    except Exception as e:
        print(f"Error fetching volume values: {e}")
    # finally:
    #     if db:
    #         db.close()  # Close MongoDB connection if open

avoid_list = ['vol', 'obs', 'ube', 'roads', 'day', 'session', 'date', 'Name', 'user', 'city', 'time']

def max_length_of_lists(data):
    max_length = 0
    for category in data:
        if category not in avoid_list:
            length = len(data[category])
            if length > max_length:
                max_length = length
    return max_length

def sum_product(data, puc_values, count):
    total_v = []
    for i in range(count):
        sum_val = 0
        for category in data:
            if category not in avoid_list:
                vehicles = data[category]
                if any('divided' in item for item in puc_values):
                    pcu = next((item['divided'] for item in puc_values if item['vehicle'] == category), 0)
                elif any('urban_express' in item for item in puc_values):
                    pcu = next((item['urban_express'] for item in puc_values if item['vehicle'] == category), 0)
                else:
                    pcu = next((item['bidirectional'] for item in puc_values if item['vehicle'] == category), 0)
                sum_val += int(vehicles[i]) * float(pcu.to_decimal())
        total_v.append(sum_val)
    return total_v


def total_cal(data, count):
    total_h = []
    for category in data:
        if category not in avoid_list:
            vehicles = data[category]
            sum_val = 0
            for i in range(count):
                value = vehicles[i]
                sum_val += int(value) if value else 0
            total_h.append(sum_val)
    return total_h

def road_cal(roadscount, HT, C):

    if roadscount == '3':
        V1 = HT[0] + HT[1] + HT[2] + HT[4]
        V2 = HT[0] + HT[2] + HT[3] + HT[5]
        V3 = HT[1] + HT[3] + HT[4] + HT[5]

        VC1 = round(V1 / C[0], 3)
        VC2 = round(V2 / C[1], 3)
        VC3 = round(V3 / C[2], 3)

        vcValues = [VC1, VC2, VC3]
        route = ['A', 'B', 'C']

    elif roadscount == '4':
        V1 = HT[0] + HT[1] + HT[2] + HT[3] + HT[6] + HT[8]
        V2 = HT[0] + HT[3] + HT[4] + HT[5] + HT[7] + HT[10]
        V3 = HT[1] + HT[4] + HT[6] + HT[7] + HT[8] + HT[11]
        V4 = HT[2] + HT[5] + HT[8] + HT[9] + HT[10] + HT[11]

        VC1 = round(V1 / C[0], 3)
        VC2 = round(V2 / C[1], 3)
        VC3 = round(V3 / C[2], 3)
        VC4 = round(V4 / C[3], 3)

        vcValues = [VC1, VC2, VC3, VC4]
        route = ['A', 'B', 'C', 'D']

    elif roadscount == '5':
        V1 = HT[0] + HT[1] + HT[2] + HT[3] + HT[4] + HT[8] + HT[12] + HT[16]
        V2 = HT[0] + HT[4] + HT[5] + HT[6] + HT[7] + HT[9] + HT[13] + HT[17]
        V3 = HT[1] + HT[5] + HT[8] + HT[9] + HT[10] + HT[11] + HT[14] + HT[18]
        V4 = HT[2] + HT[6] + HT[10] + HT[12] + HT[13] + HT[14] + HT[15] + HT[19]
        V5 = HT[3] + HT[7] + HT[11] + HT[15] + HT[16] + HT[17] + HT[18] + HT[19]

        VC1 = round(V1 / C[0], 3)
        VC2 = round(V2 / C[1], 3)
        VC3 = round(V3 / C[2], 3)
        VC4 = round(V4 / C[3], 3)
        VC5 = round(V5 / C[4], 3)

        vcValues = [VC1, VC2, VC3, VC4, VC5]
        route = ['A', 'B', 'C', 'D', 'E']

    # Find the index of the highest and lowest VC values
    highest_index = vcValues.index(max(vcValues))
    lowest_index = vcValues.index(min(vcValues))

    # Find the highest and lowest VC values and their corresponding routes
    highest_value = vcValues[highest_index]
    lowest_value = vcValues[lowest_index]

    highestroute = route[highest_index]
    lowestroute = route[lowest_index]

    # print("Highest VC value:", highest_value)
    # print("Lowest VC value:", lowest_value)
    # print("Route with highest VC value:", highestroute)
    # print("Route with lowest VC value:", lowestroute)

    return highestroute, highest_value, lowestroute, lowest_value, vcValues, route


@csrf_exempt
def analyze_data(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            puc_values = get_puc_values(data)
            # print(puc_values)
            # Find the maximum length of lists in the data
            max_length = max_length_of_lists(data)
            # print("Length of the longest list:", max_length)

            # Calculate the sum of products
            ht = sum_product(data, puc_values, max_length)
            # print("Sum of products (HT):", ht)

            # Calculate the total values for each category
            vt = total_cal(data, max_length)
            # print("Total values (VT):", vt)

            volume_list = get_volume_values()
            print(volume_list)
            capacity = []

            for i in range(len(data['vol'])):
                if int(data['vol'][i]) == 0:
                    capacity.append(1200)
                else:
                    for item in volume_list:
                        if int(data['vol'][i]) == item['id']:  
                            capacity.append(item['Volume'])
            print(capacity)
            roads = data['roads']
            a,b,c,d,v,r = road_cal(roads, ht, capacity)
            
            day = data['day']
            session = data['session']

            message = f'''Insights :: On {day} {session} The most busiest road is {a} with PUC value of {b} & 
                  The least busiest road is {c} with PUC value of {d}'''

            user = ObjectId(data['user'])
            date = data['date']
            name = data['Name']
            city = data['city']
            time = data['time']

            msg = inserting_data(user, date, name, day, session, v, r, roads, city, time, vt)

            return JsonResponse({'message': 'Data received successfully', 'result': message, 'message2': msg})
        
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {e}'})
    else:
        return JsonResponse({'error': 'Invalid request method'})
    

def inserting_data(user, date, name, day, session, v, r, roads, city, time, vt):
    try:
        db = dbconnection()  # Establish MongoDB connection
        location_collection = db['location_info']
        results_collection = db['results']

        # Check if location exists, insert if not
        location_filter = {
            "intersectionName": name,
            "city": city,
            "intersectionType": roads
        }
        location_data = location_collection.find_one(location_filter)

        if location_data is None:
            # Insert new location info
            location_id = location_collection.insert_one(location_filter).inserted_id
        else:
            location_id = location_data['_id']

        # Insert results data
        results_data = {
            "vcValues": str(v),
            "route": str(r),
            "session": session,
            "sessionDay": day,
            "sessionDate": date,
            "sessionTime": time,
            "location_id": location_id,
            "user_id": user,
            "vehicle_composition": str(vt)
        }
        results_collection.insert_one(results_data)

        msg = 'Data added successfully'
        return msg

    except Exception as e:
        print(f"Error adding data: {e}")
        msg = 'Error adding data'
        return msg

    # finally:
    #     if db:
    #         db.close()  # Close MongoDB connection if open
