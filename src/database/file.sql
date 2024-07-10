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


CREATE TABLE categories
(
    category_id integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    name character varying,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY (category_id)
);

CREATE TABLE sliders
(
    slider_id integer NOT NULL GENERATED ALWAYS AS IDENTITY,
    title character varying,
    subtitle character varying,
    link character varying,
    image_url character varying,
    published boolean,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY (slider_id)
);

INSERT INTO public.posts(title,slug,description,image_url,category_id, user_id, published, created_at, updated_at)
	VALUES ('Eyediagnose:Sistema de deteccion de retinopatia diabetica', 'eyediagnose-sistema-retinopatia', 'sss', 'assets/images/posts/i.png', 1,1,true,'Wed, 26 Jun 2024 16:41:33 GMT','Wed, 26 Jun 2024 16:41:33 GMT');


UPDATE users SET password='scrypt:32768:8:1$gIBXwkkXG5kh6BuY$b8d399926fe3ddebfbd4a17da71bac9ef02eddcc29acaa008e9191839cb1e13812111ac0b6c25a8d166e2328096eb66412b2bd4e8033df6278fd96cf2f872cb8' WHERE user_id=1;