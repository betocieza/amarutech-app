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