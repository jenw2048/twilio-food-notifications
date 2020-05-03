PRAGMA foreign_keys = ON;

/* users */
INSERT INTO users(username,business,email,password)
VALUES('wjsheng','Char Koay Teow','wjsheng@umich.edu','sha512$a45ffdcc71884853a2cba9e6bc55e812$c739cef1aec45c6e345c8463136dc1ae2fe19963106cf748baf87c7102937aa96928aa1db7fe1d8da6bd343428ff3167f4500c8a61095fb771957b4367868fb8');

INSERT INTO users(username,business,email,password)
VALUES('jialeyu','Laksa','jialeyu@umich.edu','sha512$a45ffdcc71884853a2cba9e6bc55e812$c739cef1aec45c6e345c8463136dc1ae2fe19963106cf748baf87c7102937aa96928aa1db7fe1d8da6bd343428ff3167f4500c8a61095fb771957b4367868fb8');

INSERT INTO users(username,business,email,password)
VALUES('bryancsc','IOU','bryancsc@umich.edu','sha512$a45ffdcc71884853a2cba9e6bc55e812$c739cef1aec45c6e345c8463136dc1ae2fe19963106cf748baf87c7102937aa96928aa1db7fe1d8da6bd343428ff3167f4500c8a61095fb771957b4367868fb8');


/* orders */
INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(1,'CKT with No Egg','pending','SMS',"+19299905239",'wjsheng');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(2,'CKT with extra shrimp','pending','Call',"+19299905239",'wjsheng');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(3,'Char Bihun','pending','SMS',"+19299905239",'wjsheng');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(4,'Laksa no coconut milk.','pending','Call',"+19299905239",'jialeyu');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(5,'Laksa with no mee.','pending','SMS',"+19299905239",'jialeyu');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(6,'Laksa tambah banyak.','pending','Call',"+19299905239",'jialeyu');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(7,'IOU 1','done','SMS',"+19299905239",'bryancsc');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(8,'IOU 2','pending','Call',"+19299905239",'bryancsc');

INSERT INTO orders(orderid,description,status,response_type,phone,owner)
VALUES(9,'IOU 3','pending','SMS',"+19299905239",'bryancsc');
