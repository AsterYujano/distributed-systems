# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Students: Nadia Francois
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
import requests

from threading import Thread
from random import randint
from bottle import Bottle, run, request, template

# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()
    board = {}
    values = {}

    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def threading(action, entry_element, element=''):
        payload = {'payload': element}
        path = "/propagate/"+action+"/"+str(entry_element)
        t = Thread(target=propagate_to_vessels,args=(path, payload))
        t.daemon = True
        t.start()
    
    def add_new_element_to_store(entry_element, element, is_propagated_call=False):
        global board, node_id
        success = False
        try:
            # add an element to the board of the vessel who call the function
            board[entry_element] = element
            if is_propagated_call:
                # propagate to other vessels
                threading("add", entry_element, element)
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            # modify an element in the board of the vessel who call the function
            board[entry_sequence] = modified_element
            if is_propagated_call:
                threading("modify", entry_sequence, modified_element)
                success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id
        success = False
        try:
            # delete an element to the board of the vessel who call the function
            board.pop(entry_sequence)
            if is_propagated_call:
                threading("delete", entry_sequence)
                success = True
        except Exception as e:
            print e
        return success

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                if not success:                    
                    print "\n\nCould not contact vessel {}\n\n".format(vessel_id)


    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():
        global board, node_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='Nadia Alloppi, Francois Le Pape')

    @app.get('/board')
    def get_board():
        global board, node_id
        print board
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id
        try:
            new_entry = request.forms.get('entry')
            entry_id = len(board)+1
            add_new_element_to_store(entry_id, new_entry, True)
            return True

        except Exception as e:
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        delete = request.forms.get('delete')     
        
        if delete == "0":
            #do modify
            modified_element = request.forms.get('entry') 
            modify_element_in_store(element_id, modified_element, True)
            
        if delete == "1":
            #do delete
            delete_element_from_store(element_id, True)  

        pass

    @app.post('/propagate/<action>/<element_id:int>')
    def propagation_received(action, element_id):
        global board
        payload = request.forms.get('payload')

        if action == "add":
            add_new_element_to_store(element_id, payload)

        if action == "modify":
            modify_element_in_store(element_id, payload)

        if action == "delete":
            delete_element_from_store(element_id)
        pass

    #--------------------------------------------------
    # LAB 2
    #--------------------------------------------------

    def leader_selection(body):
        try:
            leader_values = max(zip(body.values(), body.keys()))
            return leader_values[1]
        except Exception as e:
            print e
        #Gerer les conflits de valeurs

    def find_next_node(node_id):
        try:
            global vessel_list
            return vessel_list[str( (node_id % len(vessel_list))+1 )]
        except Exception as e:
            print e
    
    def mapping(body):
        global rand, node_id, leader
        print '[+] Start mapping'

        try:
            if node_id in body:
                #print '[!] Circle finished'
                leader = leader_selection(body)
                print '[!] the new leader is : ',
                print(leader)
                return

            #Append to the general list its ID and random number
            body[node_id] = rand
            print '    Body list :',
            print(body)
            next_node = find_next_node(node_id)
            path = "/propagatemapping"
            payload = {'payload': str(body)}

            # Send to next node the dictionnary
            time.sleep(0.2)
            t = Thread(target=contact_vessel,args=(next_node, path, payload))
            t.daemon = True
            t.start()
            
        except Exception as e:
            print e

    @app.post('/propagatemapping')
    def propagate_mapping():
        global board

        try:
            print '[?] Got a POST request'
            payload = eval(request.forms.get('payload'))
            print '    payload : ',
            print(payload)

            t = Thread(target=mapping,args=(payload,))
            t.daemon = True
            t.start()
        except Exception as e:
            print e

    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
        
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app, rand
        print 'Start main'
        port = 80
        parser = argparse.ArgumentParser(description='Our own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        rand = randint(0,1000)

        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            # run() will loop, so I create a thread to run the election after the mininet setup.
            # A better idea would be to emit an event when all servers are ready and then launch the election
            time.sleep(1)
            t = Thread(target=mapping,args=(dict(),))
            t.daemon = True
            t.start()
            run(app, host=vessel_list[str(node_id)], port=port)
            
        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
    traceback.print_exc()
    while True:
        time.sleep(60.)
