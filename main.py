"""
@author: Elias Kordoulas, python's butcher
@license: MIT
"""
#@if you wish to use functions directly in the code, please check out old_main.py
import json
import datetime
import plotme
import pandas as pd
from itertools import takewhile
import re

"""
#time is stored in epochs ['timestamp_ms'] so we have to make it into a date %Y %m %d
@returns a datetime.datetime object of which values can be accessed like
    .year
    .month
    .day
"""
def getDateFromTimestamp(timestamp): 
    return datetime.datetime.fromtimestamp(float(timestamp)/1e3)

#helper function for the other 2 functions that have to do with month data
def getMonthName(month): #Returns a string with the month's number
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    return months[month-1]

#@returns a list of the names of the participants
#@WHY while there is a 'participants' field it does not account for if someone was in the conversation but has since left
#thus we check every message in the list, we could do this in conjuction with another function but oh well?
def getParticipants():
    """ @return: list with participants """
    return df.sender.unique()

#@returns the length of the messagesList since it's already been sanitized and filtered to only contain messages
def getTotalMessages():
    '''@returns the length of the messagesList since it's already been sanitized and filtered to only contain messages'''
    return len(df)

#@returns the days attribute of @global variable 'diff' which is set at the loadfile() function at the bottom 
def getSpanOfConversation():
    return str(diff.days+1) + " days" # TODO: Find where this is

#@returns a dict { participantName : value }
#create a dict with keys the participants through the pList and assign 0 to it
#iterate over the mList and just increment the value for that key by 1
#@bool includeTotal is used to have a 3rd element total that holds all messages
def getTotalMessagesPerParticipant(includeTotal):
    theDict = dict.fromkeys(participantsList,0)
    for m in messagesList:
        theDict[m['sender_name']] += 1
    if(includeTotal == True):
        theDict.update({'Total' : len(messagesList)})
    return theDict

#@argument 'this' is the return of the getMessagesPerMonth() function
#@why? because we could order the dict in the perMonth function but then the data wouldn't be useful for plotting
#@returns a tuple (str, str) with the month's name and message value
def getMonthWithMostMessages(this):
    maxV = 0
    maxM = None
    for k,v in this.items():
        if v > maxV:
            maxV = v
            maxM = k
    return (maxM, str(maxV)) if maxV > 0 else None

#@returns a dict where keys are 'year + monthName' and values are ints with the ammount of messages of both participants
#ex { 2020 February : 2469}
def getMessagesPerMonth():
    perMonthDict = dict()
    for m in messagesList:
        date = getDateFromTimestamp(m['timestamp_ms'])
        key = str(date.year) +' '+ str(getMonthName(date.month)) #'2020 February'
        perMonthDict.update({key : 1 }) if key not in perMonthDict else perMonthDict.update({key : perMonthDict[key] + 1}) #{2020 February : 2469}
    return perMonthDict
    
#@returns a dict of dicts for every month that has the participants as keys and their respective messages as values
#@structure is: 
# { 
# date(y m) : { p1 : v, p2 : v }, 
# date2(y m) : { p1 : v, p2 : v } 
# }
#@access by : dict[date][participant] returns the messages of that participant for that date
def getMessagesPerMonthPerParticipant():
    theDict = {k:{} for (k,v) in getMessagesPerMonth().items()}
    for k in theDict:
        theDict[k].update({k:0 for k in participantsList})
    for m in messagesList:
        date = getDateFromTimestamp(m['timestamp_ms'])
        key = str(date.year) +' '+ str(getMonthName(date.month))
        p = m['sender_name']
        theDict[key][p] += 1
    return theDict

#@returns a dict in form of { date(y m d) : messages }
#@**kwargs is used if you want to find only the days where some words were written
#@uses 'words'=[str1, str2, str3, etc], should be a @type::set()
def getMessagesPerDay(**kwargs):
    keywords = set(kwargs['words']) if len(kwargs) > 0 else False
    from datetime import timedelta
    theDict = dict()
    for i in range (diff.days+2):
        day = sdate + timedelta(days=i)
        theDict[day.strftime('%Y %m %d')] = 0

    for m in messagesList:
        currentDay = getDateFromTimestamp(m['timestamp_ms']).strftime('%Y %m %d')
        if (keywords == False):
            theDict[currentDay] += 1
        else: #this loop is used if you want to look for specific words in each message
            if 'content' in m.keys():
                wList = set(m['content'].split())
                theDict[currentDay] += 1 if len(keywords.intersection(wList)) > 0 else 0
    return theDict
    
#@returns a dict where the keys are the dates and the values are dicts 
#@representation { date : {'participant' : messages} }
#final structures should be e.x : 
# {
# '2018 01 15' : {'p1' : 30, 'p2' : 39}, 
# '2019 09 12' : {'p1' : 39, 'p2' : 30} 
# }
def getMessagesPerDayPerParticipant():
    from datetime import timedelta
    theDict = dict()
    for i in range (diff.days+2): #should be days+1 as days+2 sometimes creates an extra day. This is a problem because of the difference in the time of day the first and last message were sent resulting in incorrect .days
        day = sdate + timedelta(days=i)
        theDict[day.strftime('%Y %m %d')] = dict.fromkeys(participantsList, 0)
    for m in messagesList:
        currentDay = getDateFromTimestamp(m['timestamp_ms']).strftime('%Y %m %d')
        theDict[currentDay][m['sender_name']] += 1
    return theDict

#@returns a list of ints that represent the seconds between the last message of a participant and the first of another
#@note does not care for ammount of participants in conversation
#@**kwargs : 'time' = type::string ex. 'Seconds', is @used for time representation and divisor since we get seconds
#@alternative, you could use the first message of someone until the first message of another but that creates
#   situations where it's not really a response but rather a new starting point for the conversation. That would
#   require contextual analysis.
#@example if someone says 'goodbye' or 'talk to you then' then it's not really a response to that last message
#@also someone could be the same one that sent the last message at let's say a week ago and then sends the next message
#   initiating the conversation again. That would skew the results as the response will be at the last message sent rather
#   than the one a week ago.
def getReponseTimePerMessage(**kwargs):
    times = {'Seconds':1, 'Minutes' : 60, 'Hours' : 3600}
    divisor = times[kwargs['time']] if len(kwargs) > 0 else 1
    myl = []
    for i in range(1,len(messagesList)):
        prev = messagesList[i-1]
        m = messagesList[i]
        if (m['sender_name'] != prev['sender_name']):
            difference = getDateFromTimestamp(m['timestamp_ms']) - getDateFromTimestamp(prev['timestamp_ms'])
            myl.append(difference.total_seconds()//divisor)
    return myl

#@returns a dict {k:v where k=participant, v=their global response time/their responses}
#@**kwargs : 'time' = type::string ex. 'Seconds', is @used for time representation and divisor since we get seconds
def getGlobalAverageResponseTimePerParticipant(**kwargs):
    times = {'Seconds' : 1, 'Minutes' : 60, 'Hours' : 60*60}
    divisor = times[kwargs['time']] if len(kwargs) > 0 else 1
    theDict = dict.fromkeys(participantsList,0)
    valuesList = [0 for k in theDict]
    #iterate over the list - 1, if the current message's sender is different than the sender of the next in
    #the list then it's considered a response to that message.
    #@caution in group conversations where multiple people respond to a message sent by one it's difficult
    #to filter out, there would need to be context awareness which is beyond the scope of this 'project'
    for i in range(0,len(messagesList)-1):
        current = messagesList[i]
        nuxt = messagesList[i+1]
        if (current['sender_name'] != nuxt['sender_name']):
            difference = getDateFromTimestamp(nuxt ['timestamp_ms']) - getDateFromTimestamp(current['timestamp_ms'])
            diffInSeconds = difference.total_seconds()
            valuesList[participantsList.index(nuxt['sender_name'])] += diffInSeconds
            theDict[nuxt['sender_name']]+=1

    for k,v in theDict.items():
        theDict[k] = round(valuesList[participantsList.index(k)] / v,2) // divisor
    return theDict

#@returns a dict where keys are each month as (year month) and values the messages for that month
#{ date : messages }
def getAverageResponseTimePerMonth(**kwargs):
    #same idea as the function above only we are now adding everything to a per month dict and do not care about
    #the participants as this is a global average of their messages
    #@reminder we take the date of the next message because that is considered the response and thus the date we increment
    times = {'Seconds' : 1, 'Minutes' : 60, 'Hours' : 60*60}
    divisor = times[kwargs['time']] if len(kwargs) > 0 else 1
    perMonthDict = dict() #@holds all the months as keys and the values will be the totalSeconds / totalMessages
    valuesList = [] #@holds the total seconds between responses for every message in a given month
    for i in range(0,len(messagesList)-1):
        current = messagesList[i]
        nuxt = messagesList[i+1]
        if (current['sender_name'] != nuxt['sender_name']):
            date = getDateFromTimestamp(nuxt['timestamp_ms'])
            difference = date - getDateFromTimestamp(current['timestamp_ms'])
            key = str(date.year) + ' ' + str(getMonthName(date.month))
            if key not in perMonthDict: #this means we've entered a new month and must initialize a new element in the array
                perMonthDict[key] = 1 
                valuesList.append(difference.total_seconds())
            else: #if in the same month update the last (and implicitly current) month in the last by the seconds it took to respond
                valuesList[len(valuesList)-1] += difference.total_seconds()
                perMonthDict[key] += 1

    i=0 #need to be able to access the list
    for k,v in perMonthDict.items():
        perMonthDict[k] = round(valuesList[i] / v,2) // divisor
        i += 1
    return perMonthDict

#@returns a dict { weekday : value } containing the messages of both participants
def getMessagesPerDayOfTheWeek():
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekDict = dict.fromkeys(weekdays,0)
    for m in messagesList:
        weekDict[weekdays[getDateFromTimestamp(m['timestamp_ms']).weekday()]] += 1
    return weekDict

#@returns a dict  { time : value } where key is the hour (13:34 is 13) and value the messages of both participants at that time 
def getMessagesPerTimeOfDay():
    timeList = [i for i in range(24)]
    timeDict = dict.fromkeys(timeList,0)
    for m in messagesList:
        timeDict[getDateFromTimestamp(m['timestamp_ms']).hour] += 1
    return timeDict

#returns a float
#ammount refers to the amount of text messages, not photos, videos etc.
def getAverageWordsPerMessage():
    wordCount = 0
    ammount = 0
    for m in messagesList:
        if 'content' in m.keys(): #to filter the messages that have text and not photos, audio etc.
            words = m['content'].split()
            wordCount += len(words)
            ammount += 1
    return round(wordCount / ammount, 2)

#@returns a dict {k:v with k:month name v:totalwordsPMonth / totalmessagesPMonth}
def getAverageWordsPerMessagePerMonth():
    perMonthDict = dict()#holds the ammount of words for each month
    prevMonth = getDateFromTimestamp(messagesList[0]['timestamp_ms']).month
    month = 0
    valuesList = [0] #holds the ammount of text messages per month to use for dividing the wordcount later
    for m in messagesList:
        date = getDateFromTimestamp(m['timestamp_ms'])
        key = str(date.year) +' '+ str(getMonthName(date.month))
        if 'content' in m.keys(): #check if it's a text message
            wordCount = len(m['content'].split())
            perMonthDict.update({key : wordCount }) if key not in perMonthDict else perMonthDict.update({key : perMonthDict[key] + wordCount})
            valuesList[month]+=1
            if(date.month != prevMonth):
                valuesList.append(1) 
                month+=1
                prevMonth = date.month
    month = 0
    for k in perMonthDict:
        perMonthDict[k] = round(perMonthDict[k] / valuesList[month], 2)

    return perMonthDict
#@returns a dict with key: sender_name | value: number:averageWords
#{ participant : averageWords }
#@messagesPerParticipant::list holds number of messages for every participant
#@averages::list holds the sum of words of every message for that participant
#@pDict::dict is the return, keys are the participants, value is totalWordsOfPar / totalMessagesOfPar
def getAverageWordsPerMessagePerParticipant():
    messagesPerParticipant = [0] * len(participantsList)
    averages = [0] * len(participantsList)
    for m in messagesList:
        if 'content' in m.keys():
            words = m['content'].split()
            averages[participantsList.index( m['sender_name'] )] += len(words)
            messagesPerParticipant[participantsList.index( m['sender_name'] )] += 1

    pDict = dict.fromkeys(participantsList)
    for i in range(len(participantsList)):
        pDict[participantsList[i]] = round(averages[i] / messagesPerParticipant[i], 2)

    return pDict

#returns a dict with typeOfMessage : value
def getMessagesPerType(): #The types are: audio_files | photos | call_duration | videos | share | gifs and if none of these, then it's a simple text message
    #Using 2 lists more than just the typesSet because we want to change the name of the keys in the final dict
    #but don't have another way to match them 
    typesSet = {"simple", "photos", "videos", "audio_files", "call_duration", "share", "gifs"}
    fixedTypesList = ['Text messages','Photos', 'Videos','Voice recordings',  'Voice calls',  'Shares', 'gifs']
    referenceList = ["simple", "photos", "videos", "audio_files", "call_duration", "share", "gifs"]
    typesDict = dict.fromkeys(fixedTypesList, 0)
    total = 0
    for message in messagesList:
        for mType in message:
            if (mType in typesSet):
                typesDict[fixedTypesList[referenceList.index(mType)]] += 1
                total += 1
                break
    
    typesDict['Text messages'] = getTotalMessages() - total #all the messages minus the special ones are the simple text ones
    return typesDict

#@returns a dict of dicts
#@structure { 
# {
# 'participant1' : {'simple' : 1, 'photos' : 145}, 
# 'participant2' : {'simple' : 4, 'photos' : 123} 
# }
#each dict contains a key that relates to the type of message and their values
def getMessagesPerTypePerParticipant():
    typesSet = {"simple", "photos", "videos", "audio_files", "call_duration", "share", "gifs"}
    fixedTypesList = ['Text messages','Photos', 'Videos','Voice recordings',  'Voice calls',  'Shares', 'gifs']
    referenceList = ["simple", "photos", "videos", "audio_files", "call_duration", "share", "gifs"] #don't do list(dict), the keys won't be in order
    #creating a dict of dicts and initalizing the k:v for that dict because dict.fromkeys() returns a reference to the same object
    dictPerParticipant = {participant: {"Text messages":0, "Photos":0, "Videos":0, "Voice recordings":0, "Voice calls":0, "Shares":0, "gifs":0} for participant in participantsList}
    
    for message in messagesList:
        for mType in message: #going over the keys of the message object dict, you'd think we should access it with 'type', well yes but not every message has a type key :)
            if (mType in typesSet): #if the set contains the type then it's increment, if not then it's a text message which carries no type identifier
                cType = fixedTypesList[referenceList.index(mType)]
                dictPerParticipant[message['sender_name']][cType] += 1
                add = False
                break
            else:
                add = True
        if (add):
            dictPerParticipant[message['sender_name']]['Text messages'] += 1
            add = False

    return dictPerParticipant

#returns a sorted dictionary containing every word and the times it was sent
def getMostCommonWords(**kwargs): 
    from collections import defaultdict
    from operator import itemgetter
    words = defaultdict(lambda :0) #this is for when a new key is added, it is assigned a value of 0
    for m in messagesList:
        if 'content' in m.keys():
            temp = m['content'].split()
            for w in temp:
                words[w] += 1
    sortedDict = dict(sorted(words.items(), key=itemgetter(1), reverse=True))

    if ('range' in kwargs.keys()):
        r = int(kwargs['range'])
        enforcedDict = dict()
        for k,v in sortedDict.items():
            if (len(enforcedDict) == r):
                return enforcedDict
            enforcedDict.update({k:v})
    return sortedDict

#@returns an int of the length of the set of mostCommonWords since it's already there
def getAmmountOfUniqueWords():
    return len(getMostCommonWords())

#@returns a sorted dict fron the getMessagesPerDay() function 
#**kwargs is for using ranger=x where x the ammount of days you'd like to see
def getDaysWithMostMessages(**kwargs):   
    most = getMessagesPerDay()
    most = {k: v for k,v in sorted(most.items(), key=lambda item: item[1], reverse=True)}
    if len(kwargs) > 0:
        enforcedDict = dict()
        for k,v in most.items():
            if (len(enforcedDict) == kwargs['range']):
                return enforcedDict
            enforcedDict.update({k:v})
    else: #not needed, added for visual clarity
        return most

#@returns a float (response time in seconds, no rounding)
#Sums all the response times for every message from the list returned by getResponseTimePerMessage()
#divides it by the length of that list since every message in that list is a response
#returns it
def getGlobalAverageResponseTime():
    temp = getReponseTimePerMessage() #returns the list in seconds
    return sum(temp)/len(temp)

#strips the other information from the messageFile, returns a list instead of dict
def dictToList(messagesFile):
    tempList = [message for message in messagesFile['messages']]
    for t in tempList: #this loop is needed for messenger's terrible choice of text encoding
        for key in t: #list of dicts { key : value }, we need to encode.decode the values
            if key == 'sender_name' or key == 'content':
                t[key] = t[key].encode('latin1').decode('utf8')
    return tempList

#@returns an int
#counts the times a word is seen in all the messages
#iterates over every message, uses.split() and searches for it in that list
#increments+1 for every time the word is found
def getWordAppearances(word):
    count = 0
    for m in messagesList:
        if ('content' in m.keys()): #needed because not every message is a text. otherwise throws KeyError
            for w in m['content'].split():
                count = count+1 if word == w else count
    return count

#literally the name, will save every available resource to a txt
#@finalstring is going to be a big effing string that holds all the information
#   it's written to the file in one big chunk at the end, ram is cheaper than write operations? idk maybe
def saveAll(filename):
    print("Saving starting, please wait..")
    import time
    stime = time.time()
    try:
        textfile = open(filename+'-stats.txt','w',encoding='utf-8')
    except:
        print("Failure to open file for writing. Exiting function")
        return None

    finalString = "Welcome to your stats for your conversation with "+filename+"\n\n"
    span = getSpanOfConversation()
    finalString+="The conversation spans "+span+" or " + str(round(float(span.split()[0])/365,2))+" years\n\n"
    if (getTotalMessages() >= 100000):
        finalString += "Wow this is a big one! You have exchanged "+str(getTotalMessages())+" messages in total!\n"
    else:
        finalString += "You have exchanged "+str(getTotalMessages())+" messages in total!\n\n"

    finalString+= "Messages breakdown:\n"
    temp = getTotalMessagesPerParticipant(False)
    for k,v in temp.items():
        finalString+="\t"+k + " : "+ str(v) +"\n"

    temp = getDaysWithMostMessages(range=5)
    finalString += "\nYour top 5 messaging days were:\n"
    for k,v in temp.items():
        finalString+="\t" + k + " : "+str(v) +"\n"

    temp = getMonthWithMostMessages(getMessagesPerMonth())
    finalString += "\nThe month with the most messages was:\n\t"+temp[0]+" with "+temp[1]+" messages\n\n"

    temp = round(getGlobalAverageResponseTime(),1) #TODO add Or X minutes 
    finalString += "Global average response time in conversation: "+str(temp)+" seconds or "+str(round(temp/60,2)) + " minutes\n\n"
    temp = getGlobalAverageResponseTimePerParticipant()
    finalString += "Average response time of each participant:\n"
    for k,v in temp.items():
        finalString+="\t" + k + " : "+str(v) +"s | " + str(round(v/60,2)) + "m\n"    
    
    temp = getMessagesPerDayOfTheWeek()
    finalString+="\nTotal messages for every day of the week:\n"
    for k,v in temp.items():
        finalString+="\t" + k + "s : "+str(v) +"\n"
    
    temp = getAverageWordsPerMessage()
    finalString+="\nAverage words per message in the conversation:\n\t"+str(temp)+"\n\n"
    temp = getAverageWordsPerMessagePerParticipant()
    finalString+="Average words in each participant's messages:\n"
    for k,v in temp.items():
        finalString+="\t" + k + " : "+str(v) +"\n"
        
    temp = getMessagesPerType()
    finalString+="\nHere are the types of messages you guys sent:\n"
    for k,v in temp.items():
        finalString+="\t" + k + " : "+str(v) +"\n"
    
    temp = getMessagesPerTypePerParticipant()
    finalString+="\nPer participant breakdown:\n"
    for k,v in temp.items(): #This is a dict with dicts inside it so..
        finalString+="\t" + k+":\n\t\t"
        for kb, kv in v.items():
            finalString+=" " + kb + " : "+str(kv)+","
        finalString+="\n"

    temp = getMostCommonWords(range=5)
    finalString+="\nYour 5 most common words were:\n"
    for k,v in temp.items():
        finalString+="\t" + k + " : "+str(v) +" times\n"
    
    temp = getAmmountOfUniqueWords()
    finalString+="\nWow you used "+str(temp)+" unique words!\n"
    
    finalString+="\n ----- END OF STATS -----"
    finalString+="\nThank you for using the analyzer!"
    textfile.write(finalString)
    textfile.close()
    ltime = time.time()
    print("----- saving took "+str(round(ltime-stime,2))+" seconds to complete -----")
    return None

# Adapts the data downloadad from WhatsApp to be more easily treated afterwards
# With regex it will detect any line break followed by a data (with the format provided by WhatsApp), that will consititute one full message
# The is a way for this to be "hacked", if one of the users ahs sent a message with with that the date format after a line break, that message will despite
# being part of anotherone will be registered as a separate message.

# example of the message mentioned: 
# (date format) - Person1: Start of the message \n(date format) The message continues\n
# 
# In this case "Start of the message" will be identified as one message and "The sessage continues" as another separate one

# This may cause a bit of trouble in the future, the optimal solution would be to leave this message with no author and then check for the one who sent 
# the previous message and assign it to the later message
def adaptData(chat):
    adaptedData = re.split('\n?\d{1,2}/\d{1,2}/\d{1,2}', chat)
    adaptedData = map(lambda x: x.split )
    return adaptedData


def getDataframe(chat):
    '''
        @chat: String with all the chat information
        @returns: Pandas Dataframe with the split information in three columns timestamp - sender - msg
    '''


    return pd.DataFrame({'timestamp' : [], 'sender': [], 'msg': []})

#****************START****************#
from os import listdir
import time

custom = None
def loadFile():
    ''' @return: A string with the load file of the chat'''
    global input_file 
    input_file = input('\nEnter the text file with the Whatsapp chat, please :)\n>> ')
    try:
        f = open(input_file, encoding='utf-8')
        chat = f.read()
        f.close()
        return chat
    except OSError:
        if (custom == "exit"):
            return
        print("File Not Found not found!")
        return loadFile()

chat = loadFile()
if (chat is None ):
    exit()

p1 = adaptData(chat)
print(p1[0:3])

# Get pandas
df = getDataframe(chat)



participantsList = getParticipants()
sdate = getDateFromTimestamp(messagesList[0]['timestamp_ms'])
ldate = getDateFromTimestamp(messagesList[len(messagesList)-1]['timestamp_ms'])
diff = ldate - sdate
value = -1
while (value != 6):
    value = input("\n1. Line Graphs\n2. Bar Graphs\n3. Radar Graphs\n4. Save all to txt\n5. Change loading folder\n6. Exit\n")
    value = int(value)
    
    if (value==1):
        svalue = int(input('''1. Messages Per Day\n2. Messages Per Day Per Participant\n3. Messages Per Day with Keywords
4. Messages Per Month\n5. Response Time Per Message\n'''))
        if (svalue==1):
            plotme.plotLineGraph_MessagesPerDay(getMessagesPerDay())
        elif(svalue==2):
            lvalue = int(input("1. One graph\n2. Separate\n"))
            if (lvalue==1):
                plotme.plotLineGraph_MessagesPerDayPerParticipant(getMessagesPerDayPerParticipant(), participantsList, False)
            elif (lvalue==2):
                plotme.plotLineGraph_MessagesPerDayPerParticipant(getMessagesPerDayPerParticipant(), participantsList, True)
        
        elif(svalue==3):
            keywords = input("Enter the words you want to find with commas ',' (ex. 'bro','boi'):\n")
            keywords = keywords.replace(" ", "").split(',')
            plotme.plotLineGraph_MessagesPerDay(getMessagesPerDay(words=keywords),keywords) 

        elif(svalue==4):
            plotme.plotLineGraph_MessagesPerMonth(getMessagesPerMonth())
        
        elif(svalue==5):
            lvalue = int(input("Time representation:\n1. Seconds\n2. Minutes\n3. Hours"))
            if (lvalue==1):
                plotme.plotLineGraph_TimeOfResponsePerMessage(getReponseTimePerMessage())
            elif (lvalue==2):
                plotme.plotLineGraph_TimeOfResponsePerMessage(getReponseTimePerMessage(time='Minutes'),time='Minutes')
            elif (lvalue==3):
                plotme.plotLineGraph_TimeOfResponsePerMessage(getReponseTimePerMessage(time='Hours'),time='Hours')

    elif (value==2):
        svalue = int(input('''1. Messages Per Month\n2. Messages Per Month Per Participant\n3. Total Messages Per Participant
4. Average Words Per Message Per Month\n5. Average Response Time Per Month\n'''))
        if (svalue==1):
            plotme.plotBarGraph_MessagesPerMonth(getMessagesPerMonth())
        elif (svalue==2):
            plotme.plotBarGraph_MessagesPerMonthPerParticipant(getMessagesPerMonthPerParticipant(),participantsList)
        elif (svalue==3):
            plotme.plotBarGraph_TotalMessages_PerParticipant(getTotalMessagesPerParticipant(True))
        elif (svalue==4):
            plotme.plotBarGraph_AveragePerMonth_General(getAverageWordsPerMessagePerMonth(),title='Words Per Message')
        elif (svalue==5):
            lvalue=int(input("Time Representation:\n1. Seconds\n2. Minutes\n3. Hours\n"))
            timeR = 'Minutes' if lvalue==2 else 'Hours' if lvalue == 3 else 'Seconds'
            plotme.plotBarGraph_MessagesPerMonth(getAverageResponseTimePerMonth(time=timeR),title='Average Response Time',time=timeR)
    elif (value==3): 
        svalue = int(input("1. Messages Per Day of the Week\n2. Messages Per Time of Day\n"))
        if (svalue == 1):
            plotme.plotSpiderGraph(getMessagesPerDayOfTheWeek())
        elif (svalue == 2): 
            plotme.plotSpiderGraph(getMessagesPerTimeOfDay())
    elif(value==4):
        saveAll(custom)

    elif (value==5): #yeah this is the way I found to return back, sue me. or maybe don't idk how the licensing for this will work yet
        messagesList = False
        while(messagesList == False):
            messagesList = loadFile()
            if (messagesList == True):
                print("Thank you for using this thing!")
                exit()
            messagesList.reverse() #the JSON files are newest first, we reverse the list to go from first to last sequentially later
            messagesFile = None
            participantsList = getParticipants()
            sdate = getDateFromTimestamp(messagesList[0]['timestamp_ms'])
            ldate = getDateFromTimestamp(messagesList[len(messagesList)-1]['timestamp_ms'])
            diff = ldate - sdate
            value = -1
    else:
        print('Thank you for using this thing! :)')
        exit()
