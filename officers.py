import streamlit as st 
import database as db 
import datetime 
from streamlit_option_menu import option_menu
import psycopg2
from caseReport import update_db
import time 
import base64


def main():
    st.write(f'<p style="color: blue; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">{db.PROJECT} - Investigators</p>', unsafe_allow_html=True)
    current,past=st.tabs(['Current Investigators','Former Investigators'])
    try:
        with current:
            left,right=current.columns([5,2])
        ###Add new Officer 
            with right.form('Officer Form',clear_on_submit=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Add New Officers</p>', unsafe_allow_html=True)
                up_id=st.text_input('ID',placeholder='Officer Id (for edit purpose)',label_visibility="collapsed")
                remove=st.checkbox('Mark left',value=False)
                officer_fname=st.text_input('First Name *')
                officer_mname=st.text_input('Middle Name ')
                officer_lname=st.text_input('Last Name *')
                contact=st.text_input('Contact Info *')
                joined_date=st.date_input('Joined Date *',max_value=datetime.datetime.now().date(),value=None)
                image=st.file_uploader('Photo',type=['jpg','jpeg','png','gif'],)
                officer_parts = [officer_fname.strip(), officer_mname.strip(), officer_lname.strip()]
                officer_name = ' '.join(part for part in officer_parts if part)  # This will join non-empty parts with a space.

                #Check for form submitted 
                if st.form_submit_button('Add',use_container_width=True):
                    if(image):
                        image=image.read() 
                    else:
                        if not up_id.strip():
                            image_path = 'icons/suspect.jpg'
                            with open(image_path, 'rb') as file:
                                image = file.read()
                        
                    label=st.empty() 
                    conn=db.connect_db()
                # If the details filled is to be updated the case runs here 
                    if up_id:
                        conn=db.connect_db()
                        #Fetch officer from database from the given id 
                        off_exists=db.from_db(conn,f"select name from officers where officer_id={up_id}")
                        if off_exists:
                            if not remove:
                                update_db(f"Update officers set name='{officer_name}' where officer_id={up_id}",officer_name.strip(),"Updated Successfully",label)
                                update_db(f"Update officers set contact='{contact}' where officer_id={up_id}",contact.strip(),"Updated Successfully",label)
                                update_db(f"Update officers set photo={psycopg2.Binary(image)} where officer_id={up_id}",image,"Updated Successfully",label)
                            else:
                                #If the officer is marked to be left or remove the officer from working force 
                                conn=db.connect_db() 
                                #See if any case is assigned to him/her
                                assigned_case=db.from_db(conn,f"select live_cases from officers where officer_id={up_id}")
                                if assigned_case[0] ==0:
                                    conn=db.connect_db() 
                                    deleted_off=db.from_db(conn,f"select * from officers where officer_id={up_id}")
                                    conn=db.connect_db() 
                                #Add the records to the ex_officers table
                                    db.run_query(conn,f"""delete from officers where officer_id={up_id};
                                                insert into ex_officers(officer_id,joined_date, left_date,contact,solved_ratio,photo,name,revised_case)
                                                values('{deleted_off[0]}','{deleted_off[5]}','{datetime.datetime.now().date()}','{deleted_off[2]}',{deleted_off[4]/deleted_off[3] if deleted_off[3]!=0 else 0},{psycopg2.Binary(deleted_off[6])},'{deleted_off[1]}',{deleted_off[7]})
                                                """,msg='Officer Removed Successfully',slot=label)
                                    time.sleep(3)
                                    label.empty() 
                                else:
                                    to_check_name=off_exists[0]+': '+str(up_id)
                                    conn=db.connect_db() 
                                    assigned_cases=db.get_all(conn,f"select caseid from casereports where investigator='{to_check_name}' and casestatus='ongoing'")
                                    label.error(f"""{off_exists[0]} has {assigned_case[0]} cases assigned. 
                                            Assign new investigator for following cases before this:
                                            {assigned_cases}
                                            """)
                                    time.sleep(3)
                                    label.empty() 
                        else:
                            label.error(f'Officer with id={up_id} doesnot exist')
                    else:
                        if not officer_fname.strip() or not officer_lname.strip() or not contact.strip() or not joined_date:
                            label.error('Fill required fiels')
                        else:
                            conn=db.connect_db() 
                            db.run_query(conn,f'''insert into officers(name,contact,joined_date,photo) values('{officer_name}','{contact}','{joined_date}',{psycopg2.Binary(image)});
                                        
                                        ''',msg='Added Successfully',slot=label)
                    time.sleep(2)
                    label.empty()

        #### Investigators REcord 
            with left.container(height=800,border=False):
                st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 25px; font-weight: bold">Investigators Record</p>', unsafe_allow_html=True)
                conn=db.connect_db() 
                officers=db.get_all(conn,"select name from officers")
                off_opt=[name for (name,) in officers ]
                search_off=st.selectbox('Search Here',options=off_opt,index=None,placeholder='Search Here',key='current',label_visibility='collapsed')
                if search_off is None:
                    conn = db.connect_db() 
                    my_officers = db.get_all(conn, "select * from officers")
                    if my_officers:
                        for i, officer in enumerate(my_officers):
                            # Alternate between columns
                            if i % 2 == 0:
                                col1, col2 = st.columns(2)

                            # Display image and details for each officer
                            with col1 if i % 2 == 0 else col2:
                                with st.container(border=True,height=400):
                                    st.write(
                                            f"""
                                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                                <img src="data:image/png;base64,{base64.b64encode(officer[6]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[1]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[5]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Involved:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: green;font-weight: bold'><b style='color: grey'> Live Cases:</b> {officer[8]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Solved:</b> {officer[4]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[7]}</p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                    else:
                        st.write('No Records Found')
                else:
                    conn = db.connect_db() 
                    my_officers = db.get_all(conn, f"select * from officers where name='{search_off}'")
                    if my_officers:
                        for i, officer in enumerate(my_officers):
                            # Alternate between columns
                            if i % 2 == 0:
                                col1, col2 = st.columns(2)

                            # Display image and details for each officer
                            with col1 if i % 2 == 0 else col2:
                                with st.container(border=True,height=400):
                                    st.write(
                                            f"""
                                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                                <img src="data:image/png;base64,{base64.b64encode(officer[6]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[1]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[5]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Involved:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: green;font-weight: bold'><b style='color: grey'> Live Cases:</b> {officer[8]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Solved:</b> {officer[4]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[7]}</p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                    else:
                        st.write('No Records Found')
        with past:
            # with st.container(border=False,height=805):
                st.write('<p style="color: white; border-bottom: 1px solid white; font-size: 25px; font-weight: bold">Investigators Record</p>', unsafe_allow_html=True)
                conn=db.connect_db() 
                officers=db.get_all(conn,"select name from ex_officers")
                off_opt=[name for (name,) in officers ]
                search_off=st.selectbox('Search Here',options=off_opt,key='former',label_visibility='collapsed',index=None,placeholder='Search Here')
                if search_off is None:
                    conn = db.connect_db() 
                    my_officers = db.get_all(conn, "select * from ex_officers")
                    if my_officers:
                        for i, officer in enumerate(my_officers):
                            # Alternate between columns
                            if i % 3 == 0:
                                col1, col2,col3 = st.columns(3)

                            # Display image and details for each officer
                            with (col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3):
                                with st.container(border=True, height=400):
                                    st.write(
                                            f"""
                                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                                <img src="data:image/png;base64,{base64.b64encode(officer[5]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;"  />
                                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[6]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[1]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Left:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Solved Ratio:</b> {officer[4]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[7]}</p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                    else:
                        st.write('No records Found')
                else:
                    conn = db.connect_db() 
                    my_officers = db.get_all(conn, f"select * from ex_officers where name='{search_off}'")
                    if my_officers:
                        for i, officer in enumerate(my_officers):
                            # Alternate between columns
                            if i % 3 == 0:
                                col1, col2,col3 = st.columns(3)

                            # Display image and details for each officer
                            with (col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3):
                                with st.container(border=True, height=400):
                                    st.write(
                                            f"""
                                            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                                                <img src="data:image/png;base64,{base64.b64encode(officer[5]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;"  />
                                                <p style='margin-bottom: 5px; font-size: 12px; font-family: sans-serif; color:grey; font-weight: bold'><b style='color:grey'>id:</b> {officer[0]}</p>
                                                <p style='margin-bottom: 2px; font-size: 20px; font-weight: bold; font-family: "Lucida Console", "Times New"; color: green;'>Name: {officer[6]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif; color:white; font-weight: bold'><b style='color:grey'>Contact:</b> {officer[3]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Joined:</b> {officer[1]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Left:</b> {officer[2]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Solved Ratio:</b> {officer[4]}</p>
                                                <p style='margin-bottom: 0px; font-size: 16px; font-family: sans-serif;color: white;font-weight: bold'><b style='color: grey'> Cases Revised:</b> {officer[7]}</p>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                    else:
                        st.write('No records Found')
    except Exception as e:
        st.warning(f'Something wrong with database {e}')

if __name__=='__main__':
    main()
