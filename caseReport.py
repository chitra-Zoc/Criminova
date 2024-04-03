import streamlit as st
import datetime
import folium
from streamlit_folium import st_folium
import database as db 
import pandas as pd 
import time 
import psycopg2
from PIL import Image 
import io 

def apply_style(row):
    if row['Case Status'] == 'ongoing':
        return ['background-color: rgba(255, 255, 0, 0.3)'] * len(row)
    elif row['Case Status'] == 'closed':
        return ['background-color: rgba(128, 128, 128, 0.3)'] * len(row)
    elif row['Case Status'] == 'solved':
        return ['background-color: rgba(50, 205, 50, 0.3)'] * len(row)
    else:
        return [''] * len(row)


def update_selected_case(selected_case):
    st.session_state.selected_case = selected_case

def update_checkbox(status): 
    st.session_state.case_status=status

def update_db(query,value,msg,place):
    here=place
    if value is not None and value != '':
        conn=db.connect_db() 
        db.run_query(conn,query,here,msg)

# if __name__=="__main__":
def case_investigation():
    # Connect to the database and fetch cases
    conn = db.connect_db()
    cases_data = db.fetch_data(conn, table_name='caseReports', data='all', fetch_attributes='caseNo,caseId,case_date,nature_of_case,case_description,caseStatus,investigator')
    conn.close()

    # Convert fetched data to pandas DataFrame
    cases_df = pd.DataFrame(cases_data, columns=['Case Number', 'Case ID', 'Date', 'Nature of Case','Case Description','Case Status','investigator'])
    case_ids = cases_df['Case ID'].tolist()

    styled_df = cases_df.style.apply(apply_style, axis=1)

    # Display the DataFrame
    st.write('<p style="color:white; border-bottom: 1px solid white; font-weight:bold; font-size: 28px; line-height: 1; margin-left: 5px">Case Records </p>', unsafe_allow_html=True)
    st.dataframe(styled_df, use_container_width=True, hide_index=True,height=150)

# Case Picker Section : 
    
    with st.container(border=True):
        st.write('<p style="color:white; border-bottom: 1px solid white; font-weight:bold; font-size: 28px; line-height: 1; margin-bottom: 15px;">Case Picker</p>', unsafe_allow_html=True)
        if 'selected_case' not in st.session_state:
            st.session_state.selected_case=None 

        # select box with all cases in the dropdown and the selected will be picked up for the investigation
        selected_case = st.selectbox('Case Picker:', options=case_ids, key="case_select",index=None,placeholder="Put case to dashboard",label_visibility="collapsed")
        update_selected_case(selected_case)        
        conn=db.connect_db()
        selected_case_data=db.fetch_data(conn,table_name='caseReports',check_attributes=f'caseId=\'{st.session_state.selected_case}\'')
        print(selected_case_data)

        if st.session_state.selected_case is not None:
            st.write('<br>',unsafe_allow_html=True )
            col1,col2=st.columns([1.5,2.5])

            with col1:
                try:    
                    m=folium.Map(location=[selected_case_data[5],selected_case_data[6]],zoom_start=17,height=200,width=200) 
                    folium.Marker([selected_case_data[5],selected_case_data[6]]).add_to(m)
                    st_folium(m,height=300,use_container_width=True)
                except:
                    st.toast('Something went wrong displaying Map')
                if 'closing_st' not in st.session_state:
                    st.session_state.closing_st=None 

                if 'case_closed' not in st.session_state:
                    st.session_state.case_closed=None 
                if(selected_case_data[8]=='solved' or selected_case_data[8]=='closed'):
                    st.session_state.case_closed=True 
                else:
                    st.session_state.case_closed=False 
                index=0
                if selected_case_data[8] =='ongoing':
                    index=0
                elif selected_case_data[8]=='solved':
                    index=1
                elif selected_case_data[8]=='closed':
                    index=2
                    st.session_state.closing_st=True 
                with st.container(border=True):
                    # update the case status here. 
                    case_status=st.radio('Case Status',options=['ongoing','solved','closed'],index=index,horizontal=True)
                    if ((case_status == 'solved' or case_status=='closed') and (selected_case_data[8]=='ongoing'))or((case_status=='ongoing') and (selected_case_data[8]=='closed' or selected_case_data[8]=='solved')):
                        st.session_state.closing_st=False 
                    else:
                        st.session_state.closing_st=True 
                    # text input for the case slosing statement. Disable if case is ongoing 
                    with st.form('Status',border=False,clear_on_submit=True):
                        closing_st=st.text_area('Final Statment',placeholder='* Case Closing Statement',label_visibility='collapsed',disabled=st.session_state.closing_st)
                        submit_final=st.form_submit_button('Confirm',disabled=st.session_state.closing_st)
                    if submit_final:
                        if closing_st !='':
                            conn=db.connect_db() 
                            msg_place=st.empty() 
                            officer_id=0
                            if selected_case_data[9] is not None:
                                officer_id=selected_case_data[9].split(': ')[1]
                        # Updates the case status and adds the report to timeline 
                            db.run_query(conn,f'''
                                         Update caseReports SET casestatus='{case_status}' where caseid='{selected_case_data[1]}';
                                         Insert into case_timeline(caseid,date,activity) values('{selected_case_data[1]}','{datetime.datetime.now().date()}','{closing_st}')
                                         ''',msg="Case Status Updated",slot=msg_place)
                            conn=db.connect_db() 
                            if case_status=='solved':
                                db.run_query(conn,f"update officers set cases_solved=cases_solved+1 where officer_id={officer_id}",slot=msg_place)
                            elif case_status=='ongoing':
                                db.run_query(conn,f"update officers set cases_revised=cases_revised+1 where officer_id={officer_id}",slot=msg_place)
                            time.sleep(2)
                            st.rerun() 
                        else:
                            st.error('Fill required field')
                s1,s2=st.columns([1,1])
                # buttons for the activity
                # will be disabled for the closed cases 
                with s1.popover('Case Update',use_container_width=True,disabled=st.session_state.case_closed):
                    with st.form('Case Update',clear_on_submit=True,border=False):
                        conn=db.connect_db()
                        db_cases=db.fetch_data(conn,fetch_attributes='nature_of_case',table_name='nature_of_case',data='all')
                        cases = [case[0] for case in db_cases]
                        nature_of_case=st.selectbox('Update Nature of Case',options=cases,placeholder=selected_case_data[3],index=None)

                        conn=db.connect_db() 
                        db_officers = db.fetch_data(conn, fetch_attributes='officer_id, name', table_name='officers', data='all')

                        # Create a dictionary to map officer names to officer IDs
                        # officers_dict = {officer[1]: officer[0] for officer in db_officers}
                        officers_options = [f"{officer[1]}: {officer[0]}" for officer in db_officers]

                        # Display the select box with officer options
                        assigned_officer = st.selectbox('Update Investigator', options=officers_options, 
                                                        placeholder='Assign Investigating Officer',index=None)

                        if st.form_submit_button('Submit',use_container_width=True):
                            place_msg=st.empty() 
                            if nature_of_case is not None and nature_of_case!=selected_case_data[3]:
                                conn=db.connect_db()
                                db.run_query(conn,f"update caseReports set nature_of_case='{nature_of_case}' where caseid='{selected_case_data[1]}'",msg='Updated to CaseReports',slot=place_msg)
                            if assigned_officer is not None and selected_case_data[9]!=assigned_officer:
                                # Extract the selected officer ID from the selected option
                                selected_officer_id = assigned_officer.split(': ')[1]
                                conn=db.connect_db() 
                                officer_cnt=db.from_db(conn,f"select contact from officers where officer_id='{selected_officer_id}'")
                                conn=db.connect_db() 
                                db.run_query(conn,f'''update caseReports set investigator='{assigned_officer}' where caseid='{selected_case_data[1]}';
                                             insert into case_timeline(date,caseid,activity) values ('{datetime.datetime.now().date()}','{selected_case_data[1]}','Officer Assigned: {assigned_officer}::Contact: {officer_cnt[0]}');
                                             update officers set cases_assigned=cases_assigned+1 where officer_id={selected_officer_id};
                                             ''',msg="Updated to timeline",slot=place_msg) 
                
                #Add the case images to database    
                    case_image=st.file_uploader('Upload Photos',type=['jpg','jpeg','png','gif'])
                    if case_image:
                            # with open(photos,"rb") as image_file:
                            image_data=case_image.read() 
                            des=st.text_input(f'Describe image',placeholder='What this image about ?')
                            if st.button('Done'):
                                place=st.empty()
                                conn=db.connect_db() 
                                db.run_query(conn,f"insert into case_images(caseid,image,description) values('{selected_case_data[1]}',{psycopg2.Binary(image_data)},'{des}')",msg='Added Successfully',slot=place)
                
                # Add the case victims 
                with s2.popover('Add Victim',use_container_width=True,disabled=st.session_state.case_closed):
                    with st.form('Victim',clear_on_submit=True,border=False):
                        victim_id=st.text_input('victim_id',placeholder="Add New or Add existing to update")
                        victim_name = st.text_input("Name: ")
                        victim_nickname = st.text_input("Nickname: ")
                        victim_gender = st.selectbox("Gender: ", ["Male", "Female", "Other"],index=None)
                        victim_address = st.text_input("Address:") 
                        victim_contact = st.text_input("Contact Information:")
                        victim_statement = st.text_area("Statement:")
                        victim_image=st.file_uploader(label='Upload Image',type=['jpg','jpeg','png','gif'])
                        victim_img=None 
                        if victim_image:    
                            victim_img=victim_image.read() 
                        if st.form_submit_button('Update'):
                            here=st.empty()
                            if victim_id is not None and victim_id !='':
                                conn=db.connect_db()
                                ids=db.fetch_data(conn,'victims',f"victim_id='{victim_id}'",'name')
                                if ids:
                                    update_db(value=victim_name,query=f"Update victims set name='{victim_name}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_nickname,query=f"Update victims set nickname='{victim_nickname}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_gender,query=f"Update victims set gender='{victim_gender}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_address,query=f"Update victims set address='{victim_address}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_contact,query=f"Update victims set contact='{victim_contact}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_statement,query=f"Update victims set statement='{victim_statement}' where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                    update_db(value=victim_img,query=f"Update victims set image={psycopg2.Binary(victim_img)} where victim_id='{victim_id}'",msg='Updated Successfully',place=here)
                                else:
                                    query = f"""
                                        INSERT INTO victims 
                                        (caseid,victim_id, name, nickname, gender, contact, address, statement, image) 
                                        VALUES 
                                        ('{selected_case_data[1]}','{victim_id}', '{victim_name}', '{victim_nickname}', '{victim_gender}', '{victim_contact}', '{victim_address}', '{victim_statement}', {psycopg2.Binary(victim_img)})
                                    """          
                                    conn=db.connect_db()
                                    db.run_query(conn,query,msg="Added Successfully",slot=here)
                                    time.sleep(2)
                                    here.empty() 
                            else:
                                placeholder=st.empty()
                                placeholder.error('No record to update !')
                                time.sleep(2)
                                placeholder.empty() 
                
                # Add the suspects 
                with s1.popover('Add Suspect',use_container_width=True,disabled=st.session_state.case_closed):
                    with st.form('Suspect',clear_on_submit=True,border=False):
                        suspect_id=st.text_input('suspect_id',placeholder="Add New or Add existing to update")
                        suspect_name = st.text_input("Name: ")
                        suspect_nickname = st.text_input("Nickname: ")
                        suspect_gender = st.selectbox("Gender: ", ["Male", "Female", "Other"],index=None)
                        suspect_address = st.text_input("Address:") 
                        suspect_contact = st.text_input("Contact Information:")
                        suspect_statement = st.text_area("Statement:")
                        suspect_image=st.file_uploader(label='Upload Image',type=['jpg','jpeg','png','gif'])
                        suspect_img=None 
                        if suspect_image:    
                            suspect_img=suspect_image.read() 
                        if st.form_submit_button('Update'):
                            msg=st.empty()
                            if suspect_id is not None and suspect_id !='':
                                conn=db.connect_db()
                                ids=db.fetch_data(conn,'suspects',f"suspect_id='{suspect_id}'",'name')
                                if ids:
                                    update_db(value=suspect_name,query=f"Update suspects set name='{suspect_name}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_nickname,query=f"Update suspects set nickname='{suspect_nickname}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_gender,query=f"Update suspects set gender='{suspect_gender}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_address,query=f"Update suspects set address='{suspect_address}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_contact,query=f"Update suspects set contact='{suspect_contact}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_statement,query=f"Update suspects set statement='{suspect_statement}' where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                    update_db(value=suspect_img,query=f"Update suspects set image={psycopg2.Binary(suspect_img)} where suspect_id='{suspect_id}'",msg='Updated Successfully',place=msg)
                                else:
                                    query = f"""
                                        INSERT INTO suspects 
                                        (caseid,suspect_id, name, nickname, gender, contact, address, statement, image) 
                                        VALUES 
                                        ('{selected_case_data[1]}','{suspect_id}', '{suspect_name}', '{suspect_nickname}', '{suspect_gender}', '{suspect_contact}', '{suspect_address}', '{suspect_statement}', {psycopg2.Binary(suspect_img)})
                                    """          
                                    conn=db.connect_db()
                                    db.run_query(conn,query,msg="Added Successfully",slot=msg)
                                    time.sleep(2)
                                    msg.empty() 
                            else:
                                placeholder=st.empty()
                                placeholder.error('No record to update !')
                                time.sleep(2)
                                placeholder.empty() 
                
                # Add the evidences 
                with s2.popover('Add Evidence ',use_container_width=True,disabled=st.session_state.case_closed):
                    with st.form('evidence *',border=False,clear_on_submit=True):
                        evidence_name=st.text_input('Evidence Identification',placeholder='Name/ Type of evidence')
                        description=st.text_area('Description',placeholder='Describe the evidence')
                        image=st.file_uploader('Evidence Image',type=['jpg','jpeg','png','gif'])
                        if st.form_submit_button('Update'):
                            label=st.empty() 
                            if evidence_name is not None and evidence_name !=' ' and description is not None and description !=' ':
                                conn=db.connect_db()
                                db.run_query(conn,f'''insert into evidence(case_id,name,description) values('{selected_case_data[1]}','{evidence_name}','{description}');
                                             insert into case_timeline(date,caseid,activity) values ('{datetime.datetime.now().date()}','{selected_case_data[1]}','Evidence Added: {evidence_name}');
                                             ''',msg='Added Successfully',slot=label)
                                if image:
                                    image=image.read()
                                    conn=db.connect_db() 
                                    db.run_query(conn,f"Update evidence set image={psycopg2.Binary(image)} where case_id='{selected_case_data[1]}' and name='{evidence_name}' and description='{description}'",msg='Updated Successfully',slot=label) 
                            else:
                                label.error('Fill the required fields')
                                time.sleep(2)
                                label.empty() 
                
                # view the saved case images 
                with st.popover('View Images',use_container_width=True):
                    conn=db.connect_db() 
                    images_data=db.fetch_data(conn,'case_images',check_attributes=f"caseid='{selected_case_data[1]}'",fetch_attributes='image,description',data='all')
                    img_dict={data[1]:data[0] for data in images_data}
                    if images_data:
                        for description,bytea in img_dict.items():
                            image=Image.open(io.BytesIO(bytea))
                            st.image(image,caption=description,width=200)
                    else:
                        st.write('No Images')
            with col2:
                #writes the description of the selected case to the dashboard 
                st.write(f'''
                    <p style="color:white; border-bottom: 1px solid white; font-weight:bold; font-size: 25px; margin-left: 100px; margin-top: 0px; line-height: 2; margin-bottom: 15px;">Case No.: {selected_case_data[0]}</p>
                    <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Case_ID      : {selected_case_data[1]}</p>
                    <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Date         : {selected_case_data[2]}</p>
                    <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Nature       : {selected_case_data[3]}</p>
                    <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 8px;">Status       : {selected_case_data[8]}</p>
                    <p style="color:grey; font-weight:bold; font-size: 20px; margin-left: 100px; line-height: 1.2; margin-bottom: 18px;">Investigator       : {selected_case_data[9]}</p>
                        ''',unsafe_allow_html=True)
                sub1,sub2=st.columns([0.5,4])

                # several case info with the exapnder that are not expanded at the first 
                with sub2.popover('Case Description',use_container_width=True):
                    st.write(f'<p style="color:red; text-align: justify">{selected_case_data[4]}</p>',unsafe_allow_html=True)
                
                with sub2.popover('Victim Info',use_container_width=True):
                    conn=db.connect_db()
                    db_victims=db.fetch_data(conn,table_name='victims',check_attributes=f"caseid='{selected_case_data[1]}'",data='all')
                    
                    for victim in db_victims:
                    # Display image of the victim in the right column
                        if victim[8] is not None:
                            image=Image.open(io.BytesIO(victim[8]))
                            st.image(image,width=200)
                        else:
                            st.image('icons/victim.jpg', width=200)
                    # Display details of the victim in the left column
                        st.write(f"<p style='margin-left: 220px; margin-top: -200px; margin-bottom: 10px; font-size: 20px; font-weight: bold; font-family: 'Lucida Console', 'Times New'; color: green;'>Name: {victim[2]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -180px; font-size: 16px; font-family: sans-serif; color: gray;'> id: {victim[1]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -170px; font-size: 16px; font-family: sans-serif; color: gray;'>Nickname: {victim[3]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -160px; font-size: 16px; font-family: sans-serif;color: gray;'>Gender: {victim[4]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -150px; font-size: 16px; font-family: sans-serif;color: gray;'>Contact: {victim[5]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -140px; font-size: 16px; font-family: sans-serif;color: gray;'>Address: {victim[6]}</p>", unsafe_allow_html=True)
                    
                
                with sub2.popover('Suspects',use_container_width=True,):
                    conn=db.connect_db()
                    db_suspects=db.fetch_data(conn,table_name='suspects',check_attributes=f"caseid='{selected_case_data[1]}'",data='all')
                    
                    for suspect in db_suspects:
                    # Display image of the victim in the right column
                        if suspect[8] is not None:
                            image=Image.open(io.BytesIO(suspect[8]))
                            st.image(image,width=200)
                        else:
                            st.image('icons/suspect.jpg', width=200)

                        st.write(f"<p style='margin-left: 220px; margin-top: -200px; margin-bottom: 10px; font-size: 20px; font-weight: bold; font-family: 'Lucida Console', 'Times New'; color: green;'>Name: {suspect[2]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -180px; font-size: 16px; font-family: sans-serif; color: gray;'> id: {suspect[1]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -170px; font-size: 16px; font-family: sans-serif; color: gray;'>Nickname: {suspect[3]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -160px; font-size: 16px; font-family: sans-serif;color: gray;'>Gender: {suspect[4]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -150px; font-size: 16px; font-family: sans-serif;color: gray;'>Contact: {suspect[5]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -140px; font-size: 16px; font-family: sans-serif;color: gray;'>Address: {suspect[6]}</p>", unsafe_allow_html=True)
                
                with sub2.popover('Gathered Evidences',use_container_width=True):
                    conn=db.connect_db()
                    evidences=db.fetch_data(conn,table_name='evidence',check_attributes=f"case_id='{selected_case_data[1]}'",data='all')
                    
                    for evidence in evidences:
                    # Display image of the victim in the right column
                        if evidence[2] is not None:
                            image=Image.open(io.BytesIO(evidence[2]))
                            st.image(image,width=200)
                        else:
                            st.image('icons/evidence.jpg', width=200)

                        st.write(f"<p style='margin-left: 220px; margin-top: -200px; margin-bottom: 10px; font-size: 20px; font-weight: bold; font-family: 'Lucida Console', 'Times New'; color: green;'>Name: {evidence[4]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -180px; font-size: 16px; font-family: sans-serif; color: gray;'> id: {evidence[0]}</p>", unsafe_allow_html=True)
                        st.write(f"<p style='margin-left: 220px; margin-top: -170px; font-size: 16px; font-family: sans-serif; color: gray;'>Description: {evidence[3]}</p>", unsafe_allow_html=True)
                                 
                with sub2.popover('Similar Cases',use_container_width=True):
                    conn=db.connect_db() 
                    same_nature_cases=db.get_all(conn,f"select caseid, case_description,case_date from caseReports where nature_of_case='{selected_case_data[3]}'")
                    conn=db.connect_db()
                    same_victim_cases=db.get_all(conn,f'''
                                            SELECT victims.caseid,case_description,case_date
                                            FROM caseReports
                                            JOIN victims ON caseReports.caseid = victims.caseid
                                            WHERE victims.name IN (
                                                SELECT name
                                                FROM victims
                                                WHERE caseid = '{selected_case_data[1]}'
                                            )
                                            AND caseReports.caseid != '{selected_case_data[1]}';
                                           ''')
                    conn=db.connect_db()
                    same_suspects_cases=db.get_all(conn,f'''
                                            SELECT suspects.caseid,case_description,case_date
                                            FROM caseReports
                                            JOIN suspects ON caseReports.caseid = suspects.caseid
                                            WHERE suspects.name IN (
                                                SELECT name
                                                FROM suspects
                                                WHERE caseid = '{selected_case_data[1]}'
                                            )
                                            AND caseReports.caseid != '{selected_case_data[1]}';
                                           ''')
                    
                    with st.expander('Same Nature'):
                        # st.write('<h3 style="color: blue;">Same Nature Cases</h3>', unsafe_allow_html=True)
                        for case in same_nature_cases:
                            st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                    f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                    f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                    '<hr>',unsafe_allow_html=True)



                    with st.expander('Same Victim'):
                        for case in same_victim_cases:
                            st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                    f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                    f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                    '<hr>',unsafe_allow_html=True)
                    with st.expander('Same Suspects'):
                        for case in same_suspects_cases:
                            st.write(f'<p><span style="color: red;"><b>Case ID:</b></span> {case[0]}</p>'
                                    f'<p><span style="color: blue;"><b>Description:</b></span> {case[1]}</p>'
                                    f'<p><span style="color: blue;"><b>Date:</b></span> {case[2]}</p>'
                                    '<hr>',unsafe_allow_html=True)
                            
                #update the case activity. What's going on ??
                with sub2.form('timeline',clear_on_submit=True,border=False):
                    timeline=st.text_area('Remarks','',label_visibility="collapsed",placeholder="Case Timeline Update. \n What's going on ??",disabled=st.session_state.case_closed,)
                    slot=sub2.empty() 
                    submit_timeline=st.form_submit_button('Add To Timeline',disabled=st.session_state.case_closed)                
                if submit_timeline:
                    if timeline !='':
                        conn=db.connect_db() 
                    # Updates the case status and adds the report to timeline 
                        db.run_query(conn,f'''
                                        Insert into case_timeline(caseid,date,activity) values('{selected_case_data[1]}','{datetime.datetime.now().date()}','{timeline}')
                                        ''',msg="Updated to timeline",slot=slot)
                        time.sleep(2)
                        st.rerun() 
                    else:
                        slot.error('Fill required field')
                # displays the case timeline inside a popover.
                with sub2.popover('View Timeline'):
                    conn=db.connect_db()
                    fetched_timeline=db.fetch_data(conn,table_name='case_timeline',check_attributes=f"caseid='{selected_case_data[1]}'",fetch_attributes='date,activity',add='order by date ASC',data='all')
                    html_content = "<style> .date { color: #3498DB; } .activity { color: #2ECC71; } </style>"
                    # Adding a title for the section
                    html_content += "<h4 style='border-bottom: 1px solid grey; line-height: 0; margin-bottom: 10px;'>Case Timeline</h4>"

                    # Iterating over each entry in the timeline
                    for date, activity in fetched_timeline:
                        # Formatting each entry with colored span tags
                        html_content += f"<p style='margin-bottom: 5px;'><span class='date'><b>{date}</b></span>: <span class='activity'>{activity}</span></p>"

                    st.markdown(html_content, unsafe_allow_html=True)
        else:           
            emp_col,s_col1,s_col2,emp_col2=st.columns([2,2,3,2])
            with s_col1:
                st.image('icons\icon.png',width=200)
            with s_col2:
                # st.markdown('<div style="text-align: center;"><img src:"icons/dashboard_empty.png" alt="Dashboard empty"></div>', unsafe_allow_html=True)
                # st.write("<img src='icons\icon.png' alt='Paris' style='width:200px'>",unsafe_allow_html=True)
                st.image('icons\dashboard_empty.png',use_column_width=True)
