CREATE DATABASE helpful;
USE helpful;
CREATE TABLE person(
			system_id int NOT NULL auto_increment,
			person_id varchar(10) NOT NULL,
			person_name varchar(30) NOT NULL,
			email varchar(255) NOT NULL,
			phone varchar(10) NOT NULL,
			
			primary key (system_id)
    );
    
CREATE TABLE customer(
			system_id int NOT NULL,
			buisness_name varchar(50),
			
			primary key (system_id),
			foreign key (system_id) references person(system_id)
    );
   
CREATE TABLE _role(
			role_id int NOT NULL,
			role_name varchar(30) NOT NULL,
			
			primary key (role_id)
    );

CREATE TABLE employee(
			system_id int NOT NULL,
			premission int NOT NULL,
			
			primary key (system_id),
			foreign key (system_id) references person(system_id),
			foreign key (premission) references _role(role_id)
    );
    
CREATE TABLE board(
			system_id int NOT NULL auto_increment,
            		board_id varchar(24) NOT NULL,
            		customer_id int,
            
            		primary key(system_id),
            		foreign key (customer_id) references customer(system_id)
	);
    
CREATE TABLE employee_board(
			employee_id int NOT NULL,
            		board_id int NOT NULL,
            
            		primary key(employee_id,board_id),
            		foreign key(employee_id) references employee(system_id),
            		foreign key(board_id) references board (system_id)
	);
    

            
