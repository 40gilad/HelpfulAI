CREATE DATABASE helpful;
USE helpful;
CREATE TABLE person(
			system_id int NOT NULL auto_increment,
			person_id varchar(10),
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
			premission int NOT NULL DEFAULT 0,
			status int NOT NULL DEFAULT 1,
			
			primary key (system_id),
			foreign key (system_id) references person(system_id),
			foreign key (premission) references _role(role_id)
    );
 
CREATE TABLE customer(
			system_id int,
			buisness_name varchar(50),
			employee_id int NOT NULL,
			backup_id int,
			leader_id int NOT NULL,
			status int NOT NULL,
			
			
			primary key (system_id),
			foreign key (employee_id) references employee(system_id),
			foreign key (backup_id) references employee(system_id),
			foreign key (leader_id) references employee(system_id)

    );
   



    
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
    
insert into _role values (1,"admin"),(2,"team_leader"),(3,"employee")
