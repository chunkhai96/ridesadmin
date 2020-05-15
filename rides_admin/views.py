from django.shortcuts import render,redirect
import pyrebase
import operator
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime, time, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
import calendar
import json 
  
f = open('firebase_config.json',) 
config = json.load(f)

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()

def login(request):
    return render(request, "login.html")

def loginValidation(request):

    email = request.POST.get("email")
    password = request.POST.get("password")
    auth = firebase.auth()
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        db = firebase.database()
        userData = db.child("User").child(user["localId"]).get().val()
        if "is_admin" in userData:
            if userData["is_admin"] == 1:
                db = firebase.database()
                uid = user['localId']
                userDetail = db.child("User").child(uid).get()
                request.session['name'] = userDetail.val()['user_profileName']
                request.session['profilePicSrc'] = userDetail.val()['user_profilePicSrc']
                return HttpResponseRedirect("/")
            else:
                msg = "You are not an admin"
                return render(request, "login.html", {"msg": msg})
        else:
            msg = "You are not an admin"
            return render(request, "login.html", {"msg": msg})
    except Exception as e:
        print(e)
        msg = "Invalid email or password"
        return render(request, "login.html", {"msg": msg})

def logout(request):
    del request.session['name']
    del request.session['profilePicSrc']
    return HttpResponseRedirect("/login")

@never_cache
def getDashboardData(request):
    db = firebase.database()
    timestampTodayMin = datetime.combine(datetime.today(), time.min).timestamp() * 1000

    todayCreatedRides = 0
    todayCompletedRides = 0
    providedRides = db.child("ProvidedRide").get().val()
    if (bool(providedRides)):
        providedRides = dict(sorted(providedRides.items(), key=lambda x: x[1]['pr_createdTimestamp'], reverse=True))
    today = datetime.today()
    currentMonth = today.replace(day=1)
    lastMonth = currentMonth.replace(day=1) - timedelta(days=1)
    lastTwoMonth = lastMonth.replace(day=1) - timedelta(days=1)
    lastThreeMonth = lastTwoMonth.replace(day=1) - timedelta(days=1)
    lastFourMonth = lastThreeMonth.replace(day=1) - timedelta(days=1)
    lastFiveMonth = lastFourMonth.replace(day=1) - timedelta(days=1)

    # Getting six month summary
    latestSixMonthSummary = {
        lastFiveMonth.strftime("%Y-%m"): [0, 0, 0], # index[0] is completed, index[1] is incomplete, index[2] is user
        lastFourMonth.strftime("%Y-%m"): [0, 0, 0],
        lastThreeMonth.strftime("%Y-%m"): [0, 0, 0],
        lastTwoMonth.strftime("%Y-%m"): [0, 0, 0],
        lastMonth.strftime("%Y-%m"): [0, 0, 0],
        currentMonth.strftime("%Y-%m"): [0, 0, 0]
    }
    if(bool(providedRides)):
        for key, val in providedRides.items():
            if val['pr_createdTimestamp'] >= timestampTodayMin:
                todayCreatedRides += 1
                if val['pr_status'] == 5:
                    todayCompletedRides += 1
            triggerMonth = datetime.fromtimestamp(int(val['pr_createdTimestamp'] / 1000)).strftime(
                '%Y-%m')
            providedRides[key].update({'triggerMonth': triggerMonth})

            if (val["triggerMonth"]) == currentMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[currentMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[currentMonth.strftime("%Y-%m")][1] += 1
            elif (val["triggerMonth"]) == lastMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[lastMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[lastMonth.strftime("%Y-%m")][1] += 1
            elif (val["triggerMonth"]) == lastTwoMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][1] += 1
            elif (val["triggerMonth"]) == lastThreeMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[lastThreeMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[lastThreeMonth.strftime("%Y-%m")][1] += 1
            elif (val["triggerMonth"]) == lastFourMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[lastFourMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[lastFourMonth.strftime("%Y-%m")][1] += 1
            elif (val["triggerMonth"]) == lastFiveMonth.strftime("%Y-%m"):
                if (val['pr_status'] == 5):
                    latestSixMonthSummary[lastFiveMonth.strftime("%Y-%m")][0] += 1
                elif(val['pr_status'] == 1):
                    latestSixMonthSummary[lastFiveMonth.strftime("%Y-%m")][1] += 1
            else:
                break
            # End of getting six month summary

    users = db.child("User").get().val()
    users = dict(sorted(users.items(), key=lambda x: x[1]['user_registerTimestamp'], reverse=True))
    todayNewUsers = 0
    todayNewUserVerification = 0

    if(bool(users)):
        for uid, userDetail in users.items():
            if userDetail['user_registerTimestamp'] >= timestampTodayMin:
                todayNewUsers += 1
            if userDetail.get('user_verifMatrixTimestamp') is not None:
                if userDetail['user_verifMatrixTimestamp'] >= timestampTodayMin and userDetail['user_verifMatrixStatus'] == 1:
                    todayNewUserVerification += 1
            elif userDetail.get('user_verifLicenseTimestamp') is not None:
                if userDetail['user_verifLicenseTimestamp'] >= timestampTodayMin and userDetail['user_verifLicenseStatus'] == 1:
                    todayNewUserVerification += 1
            userRegisterMonth = datetime.fromtimestamp(int(userDetail['user_registerTimestamp'] / 1000)).strftime(
                '%Y-%m')
            users[uid].update({'userRegisterMonth': userRegisterMonth})

            if (userDetail["userRegisterMonth"]) == currentMonth.strftime("%Y-%m"):
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
            elif (userDetail["userRegisterMonth"]) == lastMonth.strftime("%Y-%m"):
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastMonth.strftime("%Y-%m")][2] += 1
            elif (userDetail["userRegisterMonth"]) == lastTwoMonth.strftime("%Y-%m"):
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][2] += 1
            elif (userDetail["userRegisterMonth"]) == lastThreeMonth.strftime("%Y-%m"):
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastThreeMonth.strftime("%Y-%m")][2] += 1
            elif (userDetail["userRegisterMonth"]) == lastFourMonth.strftime("%Y-%m"):
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastThreeMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastFourMonth.strftime("%Y-%m")][2] += 1
            else:
                latestSixMonthSummary[currentMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastTwoMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastThreeMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastFourMonth.strftime("%Y-%m")][2] += 1
                latestSixMonthSummary[lastFiveMonth.strftime("%Y-%m")][2] += 1


    context = {
        "todayNewUsers": todayNewUsers,
        "todayNewUserVerification": todayNewUserVerification,
        "todayCreatedRides": todayCreatedRides,
        "todayCompletedRides": todayCompletedRides,
        "latestSixMonthSummary": latestSixMonthSummary
    }
    return render(request, "dashboard.html", context)

@never_cache
def getUserVerificationData(request):
    db = firebase.database()
    users = db.child("User").get().val()
    pendingVerifs = {}
    for uid, userDetail in users.items():
        if userDetail.get('user_verifMatrixStatus') is not None and userDetail.get('user_verifLicenseStatus') is not None:
            if userDetail['user_verifMatrixStatus'] == 1:
                pendingVerifs[uid] = userDetail
            elif userDetail['user_verifLicenseStatus'] == 1:
                pendingVerifs[uid] = userDetail
        elif userDetail.get('user_verifLicenseStatus') is not None:
            if userDetail['user_verifLicenseStatus'] == 1:
                pendingVerifs[uid] = userDetail
        elif userDetail.get('user_verifMatrixStatus') is not None :
            if userDetail['user_verifMatrixStatus'] == 1:
                pendingVerifs[uid] = userDetail

    context = {
        "pendingVerifs": pendingVerifs
    }
    return render(request, "user_verification.html", context)

def verifyUserMatrix(request):
    uid = request.GET.get('uid')
    status = "Failed"
    if uid is not None:
        db = firebase.database()
        try:
            db.child("User").child(uid).update({"user_verifMatrixStatus": 2})
            status = "Success"
        except:
            status = "Failed"
    return HttpResponse(status)

def rejectUserMatrix(request):
    uid = request.GET.get('uid')
    status = "Failed"
    if uid is not None:
        db = firebase.database()
        try:
            db.child("User").child(uid).update({"user_verifMatrixStatus": 3})
            status = "Success"
        except:
            status = "Failed"
    return HttpResponse(status)

def verifyUserLicense(request):
    uid = request.GET.get('uid')
    status = "Failed"
    if uid is not None:
        db = firebase.database()
        try:
            db.child("User").child(uid).update({"user_verifLicenseStatus": 2})
            status = "Success"
        except:
            status = "Failed"
    return HttpResponse(status)

def rejectUserLicense(request):
    uid = request.GET.get('uid')
    status = "Failed"
    if uid is not None:
        db = firebase.database()
        try:
            db.child("User").child(uid).update({"user_verifLicenseStatus": 3})
            status = "Success"
        except:
            status = "Failed"
    return HttpResponse(status)

@never_cache
def getAllUsers(request):
    db = firebase.database()
    users = db.child("User").get().val()

    context = {
        "users": users
    }
    return render(request, "user.html", context)

@never_cache
def getAllRides(request):
    db = firebase.database()
    rides = {}
    pyreRides = db.child("ProvidedRide").get()
    if(pyreRides.each()):
        for pr in pyreRides.each():
            rides[pr.key()] = pr.val()
            departDatetime = datetime.fromtimestamp(int(pr.val()['pr_departTimestamp'] / 1000)).strftime('%Y-%m-%d %H:%M')
            rides[pr.key()].update({'departDatetime': departDatetime})
            pyreSharedRide = db.child("SharedRide").order_by_child("rs_providedRideId").equal_to(pr.key()).get()
            numOfCarpooler = 0
            for sr in pyreSharedRide.each():
                if (sr.val()["rs_status"] == 3 or sr.val()["rs_status"] == 5):
                    numOfCarpooler += 1
            rides[pr.key()].update({'numOfCarpooler': numOfCarpooler})

    context = {
        "rides": rides
    }
    return render(request, "ride.html", context)

@never_cache
def getUserDetail(request):
    uid = request.GET.get('uid')
    db = firebase.database()

    user = db.child("User").child(uid).get().val()
    user['registerDatetime'] = datetime.fromtimestamp(int(user['user_registerTimestamp'] / 1000)).strftime('%Y-%m-%d %H:%M')
    if ('user_profilePicSrc' not in user):
        user['user_profilePicSrc'] = ""

    emergencyContacts = db.child("EmergencyContact").child(uid).get().val()

    #Getting user rating review
    userRatingReviews = {}
    pyreRatingReviews = db.child("RatingReview").order_by_child("rr_receiverUid").equal_to(uid).get()
    totalRatingPoint = 0
    starCounting ={
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }
    for ratingReview in pyreRatingReviews.each():
        userRatingReviews[ratingReview.key()] = ratingReview.val()
        userRatingReviews[ratingReview.key()].update({'starLoopYellow': range(ratingReview.val()['rr_rating'])})
        userRatingReviews[ratingReview.key()].update({'starLoopGrey': range(5 - ratingReview.val()['rr_rating'])})
        rateDatetime = datetime.fromtimestamp(int(ratingReview.val()['rr_createdTimeStamp'] / 1000)).strftime('%Y-%m-%d %H:%M')
        userRatingReviews[ratingReview.key()].update({'rateDatetime': rateDatetime})
        raterDetail = db.child("User").child(ratingReview.val()['rr_raterUid']).get().val()
        userRatingReviews[ratingReview.key()].update({'raterProfileName': raterDetail['user_profileName']})
        if('user_profilePicSrc' in raterDetail):
            userRatingReviews[ratingReview.key()].update({'raterProfileImageSrc': raterDetail['user_profilePicSrc']})
        totalRatingPoint += ratingReview.val()["rr_rating"]
        if ratingReview.val()['rr_rating'] == 1:
            starCounting["1"] +=1
        elif ratingReview.val()['rr_rating'] == 2:
            starCounting["2"] += 1
        elif ratingReview.val()['rr_rating'] == 3:
            starCounting["3"] += 1
        elif ratingReview.val()['rr_rating'] == 4:
            starCounting["4"] += 1
        elif ratingReview.val()['rr_rating'] == 5:
            starCounting["5"] += 1

    if (len(userRatingReviews) > 0):
        percentOneStar = int((starCounting["1"] / len(userRatingReviews)) * 100)
        percentTwoStar = int((starCounting["2"] / len(userRatingReviews)) * 100)
        percentThreeStar = int((starCounting["3"] / len(userRatingReviews)) * 100)
        percentFourStar = int((starCounting["4"] / len(userRatingReviews)) * 100)
        percentFiveStar = int((starCounting["5"] / len(userRatingReviews)) * 100)
    else:
        percentOneStar = 0
        percentTwoStar = 0
        percentThreeStar = 0
        percentFourStar = 0
        percentFiveStar = 0


    userRatingReviews = dict(sorted(userRatingReviews.items(), key=lambda x: x[1]['rr_createdTimeStamp'], reverse=True));

    if(userRatingReviews):
        avgRatingPoint = totalRatingPoint/len(userRatingReviews)
    else:
        avgRatingPoint = 0
    # End of getting user rating review

    userVehicles = {}
    pyreVehicle = db.child("Vehicle").order_by_child("vehicle_uid").equal_to(uid).get()
    for vehicle in pyreVehicle.each():
        userVehicles[vehicle.key()] = vehicle.val()


    #Getting user related ride
    rideCompleted = 0
    incompleteRide = 0
    userRelatedRides = {}
    userSharedRides = {}
    userProvidedRides = {}
    pyreSharedRide = db.child("SharedRide").order_by_child("rs_carpoolerUid").equal_to(uid).get()
    for sr in pyreSharedRide.each():
        userSharedRides[sr.key()] = sr.val()
        rideDetail = db.child("ProvidedRide").child(sr.val()['rs_providedRideId']).get()
        userRelatedRides[rideDetail.key()] = dict(rideDetail.val())
        userTriggerDatetime = datetime.fromtimestamp(int(sr.val()['rs_createdTimestamp']/1000)).strftime('%Y-%m-%d %H:%M')
        departDatetime = datetime.fromtimestamp(int(rideDetail.val()['pr_departTimestamp'] / 1000)).strftime(
            '%Y-%m-%d %H:%M')
        departMonth = datetime.fromtimestamp(int(sr.val()['rs_createdTimestamp'] / 1000)).strftime(
            '%b %Y')
        userRelatedRides[rideDetail.key()].update({'userTriggerDatetime': userTriggerDatetime})
        userRelatedRides[rideDetail.key()].update({'departDatetime': departDatetime})
        userRelatedRides[rideDetail.key()].update({'departMonth': departMonth})
        userRelatedRides[rideDetail.key()].update({'userRole': 'carpooler'})
        userRelatedRides[rideDetail.key()].update({'userStatus': sr.val()['rs_status']})
        if(sr.val()['rs_status'] == 5):
            rideCompleted += 1
        elif (sr.val()['rs_status'] == 3):
            incompleteRide += 1

    pyreProvidedRide = db.child("ProvidedRide").order_by_child("pr_providerUid").equal_to(uid).get()
    for pr in pyreProvidedRide.each():
        userProvidedRides[pr.key()] = pr.val()
        userRelatedRides[pr.key()] = pr.val()
        userTriggerDatetime = datetime.fromtimestamp(int(pr.val()['pr_createdTimestamp'] / 1000)).strftime(
            '%Y-%m-%d %H:%M')
        departDatetime = datetime.fromtimestamp(int(pr.val()['pr_departTimestamp'] / 1000)).strftime(
            '%Y-%m-%d %H:%M')
        departMonth = datetime.fromtimestamp(int(pr.val()['pr_departTimestamp'] / 1000)).strftime(
            '%b %Y')
        userRelatedRides[pr.key()].update({'userTriggerDatetime': userTriggerDatetime})
        userRelatedRides[pr.key()].update({'departDatetime': departDatetime})
        userRelatedRides[pr.key()].update({'departMonth': departMonth})
        userRelatedRides[pr.key()].update({'userRole': 'driver'})
        if (pr.val()['pr_status'] == 5):
            rideCompleted += 1
        elif (pr.val()['pr_status'] == 1):
            incompleteRide += 1
    #End of getting user related ride

    #Getting userLatestThreeMonthSummary
    today = datetime.today()
    currentMonth = today.replace(day=1)
    lastMonth = currentMonth.replace(day=1) - timedelta(days=1)
    lastTwoMonth = lastMonth.replace(day=1) - timedelta(days=1)

    userLatestThreeMonthSummary = {
        lastTwoMonth.strftime("%b"): [0, 0], #index[0] is driver index[1] is carpooler
        lastMonth.strftime("%b"): [0, 0],
        currentMonth.strftime("%b"): [0, 0]
    }

    userRelatedRides = dict(sorted(userRelatedRides.items(), key=lambda x: x[1]['departDatetime'], reverse=True))
    for key, val in userRelatedRides.items():
        rideDepartDatetime = datetime.fromtimestamp(int(val['pr_departTimestamp']/1000))
        if(rideDepartDatetime.year > today.year):
            continue
        elif(rideDepartDatetime.month > today.month):
            continue
        if(val["departMonth"]) == currentMonth.strftime("%b %Y"):
            if(val["userRole"] == "driver"):
                if (val['pr_status'] == 1 or val['pr_status'] == 5):
                    userLatestThreeMonthSummary[currentMonth.strftime("%b")][0] += 1
            elif (val["userRole"] == "carpooler"):
                if (val['userStatus'] == 3 or val['userStatus'] == 5):
                    userLatestThreeMonthSummary[currentMonth.strftime("%b")][1] += 1
        elif (val["departMonth"]) == lastMonth.strftime("%b %Y"):
            if (val["userRole"] == "driver"):
                if (val['pr_status'] == 1 or val['pr_status'] == 5):
                    userLatestThreeMonthSummary[lastMonth.strftime("%b")][0] += 1
            elif (val["userRole"] == "carpooler"):
                if (val['userStatus'] == 3 or val['userStatus'] == 5):
                    userLatestThreeMonthSummary[lastMonth.strftime("%b")][1] += 1
        elif (val["departMonth"]) == lastTwoMonth.strftime("%b %Y"):
            if (val["userRole"] == "driver"):
                if (val['pr_status'] == 1 or val['pr_status'] == 5):
                    userLatestThreeMonthSummary[lastTwoMonth.strftime("%b")][0] += 1
            elif (val["userRole"] == "carpooler"):
                if (val['userStatus'] == 3 or val['userStatus'] == 5):
                    userLatestThreeMonthSummary[lastTwoMonth.strftime("%b")][1] += 1
        else:
            break
    #End of getting userLatestThreeMonthSummary

    userRelatedRides = dict(sorted(userRelatedRides.items(), key=lambda x: x[1]['userTriggerDatetime'],reverse=True))

    context = {
        "user": user,
        "emergencyContacts": emergencyContacts,
        "userRatingReviews": userRatingReviews,
        "avgRatingPoint": avgRatingPoint,
        "userLatestThreeMonthSummary": userLatestThreeMonthSummary,
        "statusOneStar": {"count": starCounting["1"], "percent": percentOneStar},
        "statusTwoStar": {"count": starCounting["2"], "percent": percentTwoStar},
        "statusThreeStar": {"count": starCounting["3"], "percent": percentThreeStar},
        "statusFourStar": {"count": starCounting["4"], "percent": percentFourStar},
        "statusFiveStar": {"count": starCounting["5"], "percent": percentFiveStar},
        "userVehicles": userVehicles,
        "rideCompleted": rideCompleted,
        "incompleteRide": incompleteRide,
        "userRelatedRides": userRelatedRides
    }

    return render(request, "userDetail.html", context)

@never_cache
def getRideDetail(request):
    rideId = request.GET.get('rideId')
    db = firebase.database()
    rideDetail = db.child("ProvidedRide").child(rideId).get().val()
    rideDetail["createDatetime"] = datetime.fromtimestamp(int(rideDetail['pr_createdTimestamp'] / 1000)).strftime(
        '%Y-%m-%d %H:%M')
    rideDetail["departDatetime"] = datetime.fromtimestamp(int(rideDetail['pr_departTimestamp'] / 1000)).strftime(
        '%Y-%m-%d %H:%M')

    provider = db.child("User").child(rideDetail["pr_providerUid"]).get().val()
    providerProfileName = provider["user_profileName"]
    if('user_profilePicSrc' in provider):
        providerProfilePicSrc = provider['user_profilePicSrc']
    else:
        providerProfilePicSrc = ""

    sharedRides = {}
    pyreSharedRide = db.child("SharedRide").order_by_child("rs_providedRideId").equal_to(rideId).get()
    for sr in pyreSharedRide.each():
        if(sr.val()["rs_status"] == 3 or sr.val()["rs_status"] == 5):
            sharedRides[sr.key()] = sr.val()
            carpooler = db.child("User").child(sr.val()["rs_carpoolerUid"]).get().val()
            sharedRides[sr.key()].update({'carpoolerProfileName': carpooler['user_profileName']})
            if("user_profilePicSrc" in carpooler):
                sharedRides[sr.key()].update({'carpoolerProfilePicSrc': carpooler['user_profilePicSrc']})
            else:
                sharedRides[sr.key()].update({'carpoolerProfilePicSrc': ""})

    rideDiscussions = {}
    pyreDiscussions = db.child("Discussion").child(rideId).get()
    if pyreDiscussions.each() is not None:
        for discussion in pyreDiscussions.each():
            rideDiscussions[discussion.key()] = discussion.val()
            msgDatetime = datetime.fromtimestamp(int(discussion.val()['disc_timestamp'] / 1000)).strftime(
                '%Y-%m-%d %H:%M')
            rideDiscussions[discussion.key()].update({'msgDatetime': msgDatetime})
            sender = db.child("User").child(discussion.val()["disc_sender"]).get().val()
            rideDiscussions[discussion.key()].update({'senderProfileName': sender['user_profileName']})
            if("user_profilePicSrc" in sender):
                rideDiscussions[discussion.key()].update({'senderProfilePicSrc': sender['user_profilePicSrc']})
            else:
                rideDiscussions[discussion.key()].update({'senderProfilePicSrc': ""})

    vehicle = db.child("Vehicle").child(rideDetail["pr_vehicleId"]).get().val()


    context = {
        "rideId": rideId,
        "rideDetail": rideDetail,
        "providerProfileName": providerProfileName,
        "providerProfilePicSrc": providerProfilePicSrc,
        "sharedRides": sharedRides,
        "rideDiscussions": rideDiscussions,
        "vehicle": vehicle
    }
    return render(request, "rideDetail.html", context)

@never_cache
def positionTracking(request):
    rideId = request.GET.get('rideId')
    uid = request.GET.get('uid')
    db = firebase.database()
    locationTracking = {}
    pyreLocationTracking = db.child("Location Tracking").child(rideId).child(uid).get()

    if pyreLocationTracking.each() is not None:
        for lt in pyreLocationTracking.each():
            locationTracking[lt.key()] = lt.val()
            trackingDatetime = datetime.fromtimestamp(int(int(lt.key()) / 1000)).strftime(
                '%Y-%m-%d %H:%M')
            locationTracking[lt.key()].update({'trackingDatetime': trackingDatetime})

    rideDetail = db.child("ProvidedRide").child(rideId).get().val()


    context = {
        "locationTracking": locationTracking,
        "rideDetail": rideDetail
    }

    return render(request, "positionTracking.html", context)
