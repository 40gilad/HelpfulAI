CREATE DATABASE helpful;
USE helpful;
CREATE TABLE person(
			system_id int NOT NULL auto_increment,
			person_id varchar(12),
			person_name varchar(30) NOT NULL,
			email varchar(255) NOT NULL,
			phone varchar(10) NOT NULL,
			
			primary key (person_id),
            		unique  (system_id),
			unique (phone)
		
    );
    
   
CREATE TABLE _role(
			role_id int,
			role_name varchar(30) NOT NULL,
			
			primary key (role_id)
    );

CREATE TABLE employee(
			system_id int,
			premission int NOT NULL,
			status int NOT NULL DEFAULT 1,
			
			primary key (system_id),
			foreign key (system_id) references person(system_id),
			foreign key (premission) references _role(role_id)
    );
 
CREATE TABLE customer(
			system_id int primary key,
			buisness_name varchar(50),
			status int NOT NULL DEFAULT 1,
			
			foreign key (system_id) references person(system_id)

    );
   



CREATE TABLE conversations(
			conv_id VARCHAR(255) primary key,
			conv_name VARCHAR(255) NOT NULL,
			customer_id int NOT NULL,
			employee_id int NOT NULL,
			backup_id int,
			leader_id int,
			
			foreign key (customer_id) references person (system_id),
			foreign key (employee_id) references person (system_id),
			foreign key (backup_id) references person (system_id),
			foreign key (leader_id) references person (system_id)
	);
    



CREATE TABLE messages (
    			msg_id VARCHAR(255),
    			conv_id VARCHAR(255),
    			quoted_phone VARCHAR(20) NOT NULL,
    			quoter_phone VARCHAR(20) NOT NULL,
    			content TEXT,
    			ack_timestamp VARCHAR(40),
    			status INT NOT NULL CHECK (status IN (1, 0)) DEFAULT 0,


			primary key (msg_id,quoter_phone,quoted_phone)

	);


create table sessions(
			system_id int NOT NULL primary key,
			stage int NOT NULL DEFAULT 0,
                        
                        foreign key (system_id) references person(system_id)
	);

create table daily_answers (
            msg_id VARCHAR(255) primary key,
            quoted_phone VARCHAR(12),
            status INT NOT NULL CHECK (status IN (1, 0)) DEFAULT 0
    );

create table sent_messages (
            msg_id VARCHAR(255),
            quoter_phone VARCHAR(12) primary key
    );

insert into _role values (1,"admin"),(2,"team_leader"),(3,"employee");

insert into person (person_id,person_name,email,phone)
	values("313416562","Gilad Meir","gilad@helpfulpro.biz","0526263862"),
	("123456","Yonatan Meir","yona@gmail.com","0528449529"),
	("1111","Dovi","yossi@waf.com","123456789"),
	("2222","Maggie","mikky@waf.com","987654321");

insert into employee (system_id,premission)
	select
	 (select system_id from person where person_id="313416562"),
	(select role_id from _role where role_name="employee");

insert into customer (system_id,buisness_name)
	select
	(select system_id from person where person_id="123456"),"yona's buisness";
	
insert into conversations (conv_id,conv_name,customer_id,employee_id)
	select 
	"120363198441376106@g.us","Yauu",
	(select system_id from person where phone="0528449529"),
	(select system_id from person where phone="0526263862");

insert into messages(msg_id,conv_id,quoted_phone,quoter_phone,content)
	values("1111","2222","987654","3210","manual insrtion from mysql for QA");


insert into sessions(system_id)
	values(1);








/*
    
CREATE TABLE board(
			system_id int NOT NULL auto_increment,
            		board_id varchar(24) NOT NULL,
            		customer_id int,
            
            		primary key(board_id),
                    unique (system_id),
            		foreign key (customer_id) references customer(system_id)
	);
    
CREATE TABLE employee_board(
			employee_id int,
            		board_id int,
            
            		primary key(employee_id,board_id),
            		foreign key(employee_id) references employee(system_id),
            		foreign key(board_id) references board (system_id)
	);

*/
    

