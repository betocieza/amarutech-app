CREATE TABLE users
(
    user_id integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    first_name character varying,
    last_name character varying,
    email character varying,
    username character varying,
    password character varying,
    enabled boolean,
    PRIMARY KEY (user_id)
);

INSERT INTO public.users(
	first_name, last_name, email, username, password, enabled)
	VALUES ('Edilberto', 'Vasquez', 'evasquez@amarutech.net', 'evasquez', 'scrypt:32768:8:1$Q0YsJSjmCtZVSqEP$2b1a4c1906ce912a3adaa6bcb6bfa664cd219ebb738da14e9db2e9f596cda465dbb6a01a3b692582d67d7f937064aecf1dbd6ae452bd300be34f16a7ce4f4598',true);


CREATE TABLE posts
(
    post_id integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    title character varying,
    slug character varying,
    description character varying,
    image_url character varying,
    category_id integer,
    user_id integer,
    published boolean,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY (post_id)
);

INSERT INTO public.posts(title,slug,description,image_url,category_id, user_id, published, created_at, updated_at)
	VALUES ('Eyediagnose:Sistema de deteccion de retinopatia diabetica', 'eyediagnose-sistema-retinopatia', 'sss', 'assets/images/posts/i.png', 1,1,true,'Wed, 26 Jun 2024 16:41:33 GMT','Wed, 26 Jun 2024 16:41:33 GMT');
UPDATE posts SET image_url='https://amarutech-files.s3.us-west-002.backblazeb2.com/eyediagnose.png' WHERE post_id=1;