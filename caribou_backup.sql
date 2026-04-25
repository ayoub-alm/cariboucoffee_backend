--
-- PostgreSQL database dump
--

\restrict rAEjlS0x8O4RmHcgsDD6bF0x96u2cJzQB7olViwdAbX0aplpbvgOIGBJf0mEc58

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auditstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.auditstatus AS ENUM (
    'IN_PROGRESS',
    'COMPLETED'
);


ALTER TYPE public.auditstatus OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'AUDITOR',
    'VIEWER',
    'MANAGER',
    'BOSS'
);


ALTER TYPE public.userrole OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: audit_answers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_answers (
    id integer NOT NULL,
    value integer,
    choice character varying,
    comment character varying,
    audit_id integer,
    question_id integer,
    photo_url character varying
);


ALTER TABLE public.audit_answers OWNER TO postgres;

--
-- Name: audit_answers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_answers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_answers_id_seq OWNER TO postgres;

--
-- Name: audit_answers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_answers_id_seq OWNED BY public.audit_answers.id;


--
-- Name: audit_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_categories (
    id integer NOT NULL,
    name character varying,
    description character varying,
    icon character varying,
    display_order integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.audit_categories OWNER TO postgres;

--
-- Name: audit_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_categories_id_seq OWNER TO postgres;

--
-- Name: audit_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_categories_id_seq OWNED BY public.audit_categories.id;


--
-- Name: audit_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_questions (
    id integer NOT NULL,
    text character varying,
    weight integer,
    category_id integer,
    correct_answer character varying,
    na_score integer,
    display_order integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.audit_questions OWNER TO postgres;

--
-- Name: audit_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_questions_id_seq OWNER TO postgres;

--
-- Name: audit_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_questions_id_seq OWNED BY public.audit_questions.id;


--
-- Name: audits; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audits (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    score double precision,
    coffee_id integer,
    auditor_id integer,
    shift character varying,
    staff_present character varying,
    actions_correctives character varying,
    training_needs character varying,
    purchases character varying,
    photo_url character varying,
    status character varying DEFAULT 'COMPLETED'::character varying,
    date timestamp with time zone
);


ALTER TABLE public.audits OWNER TO postgres;

--
-- Name: audits_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audits_id_seq OWNER TO postgres;

--
-- Name: audits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audits_id_seq OWNED BY public.audits.id;


--
-- Name: coffees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coffees (
    id integer NOT NULL,
    name character varying,
    location character varying,
    active boolean,
    ref character varying
);


ALTER TABLE public.coffees OWNER TO postgres;

--
-- Name: coffees_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.coffees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.coffees_id_seq OWNER TO postgres;

--
-- Name: coffees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.coffees_id_seq OWNED BY public.coffees.id;


--
-- Name: manager_coffees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.manager_coffees (
    user_id integer NOT NULL,
    coffee_id integer NOT NULL
);


ALTER TABLE public.manager_coffees OWNER TO postgres;

--
-- Name: user_rights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_rights (
    id integer NOT NULL,
    user_id integer NOT NULL,
    coffees_read boolean DEFAULT false NOT NULL,
    coffees_create boolean DEFAULT false NOT NULL,
    coffees_update boolean DEFAULT false NOT NULL,
    coffees_delete boolean DEFAULT false NOT NULL,
    audits_read boolean DEFAULT false NOT NULL,
    audits_create boolean DEFAULT false NOT NULL,
    audits_update boolean DEFAULT false NOT NULL,
    audits_delete boolean DEFAULT false NOT NULL,
    users_read boolean DEFAULT false NOT NULL,
    users_create boolean DEFAULT false NOT NULL,
    users_update boolean DEFAULT false NOT NULL,
    users_delete boolean DEFAULT false NOT NULL,
    categories_read boolean DEFAULT false NOT NULL,
    categories_create boolean DEFAULT false NOT NULL,
    categories_update boolean DEFAULT false NOT NULL,
    categories_delete boolean DEFAULT false NOT NULL,
    questions_read boolean DEFAULT false NOT NULL,
    questions_create boolean DEFAULT false NOT NULL,
    questions_update boolean DEFAULT false NOT NULL,
    questions_delete boolean DEFAULT false NOT NULL
);


ALTER TABLE public.user_rights OWNER TO postgres;

--
-- Name: user_rights_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_rights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_rights_id_seq OWNER TO postgres;

--
-- Name: user_rights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_rights_id_seq OWNED BY public.user_rights.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying,
    hashed_password character varying,
    full_name character varying,
    is_active boolean,
    role public.userrole,
    coffee_id integer,
    receive_daily_report boolean DEFAULT false,
    receive_weekly_report boolean DEFAULT false,
    receive_monthly_report boolean DEFAULT false
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_answers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_answers ALTER COLUMN id SET DEFAULT nextval('public.audit_answers_id_seq'::regclass);


--
-- Name: audit_categories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_categories ALTER COLUMN id SET DEFAULT nextval('public.audit_categories_id_seq'::regclass);


--
-- Name: audit_questions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_questions ALTER COLUMN id SET DEFAULT nextval('public.audit_questions_id_seq'::regclass);


--
-- Name: audits id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audits ALTER COLUMN id SET DEFAULT nextval('public.audits_id_seq'::regclass);


--
-- Name: coffees id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coffees ALTER COLUMN id SET DEFAULT nextval('public.coffees_id_seq'::regclass);


--
-- Name: user_rights id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_rights ALTER COLUMN id SET DEFAULT nextval('public.user_rights_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
a1b2c3d4e5f6
\.


--
-- Data for Name: audit_answers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_answers (id, value, choice, comment, audit_id, question_id, photo_url) FROM stdin;
57241	3	oui		24	26	\N
57242	3	oui		24	27	\N
57243	2	oui		24	28	\N
57244	2	oui		24	29	\N
57245	3	oui		24	30	\N
57246	3	oui		24	31	\N
57247	1	oui		24	32	\N
57248	1	oui		24	33	\N
57249	1	oui		24	34	\N
57250	4	oui	Parfait	24	35	["/static/uploads/c8665594-446a-47fe-ad65-f8d815215552.jpg"]
57251	3	oui		24	36	\N
57252	4	oui		24	38	\N
57253	1	oui		24	39	\N
57254	5	oui		24	40	\N
57255	5	oui	Besoin d’une boîte alimentaire pour remplacer celle du réfrigérateur.	24	41	["/static/uploads/f7c20105-26b5-4fe5-a734-a0eb3989d948.jpg"]
57256	2	oui		24	42	\N
57257	2	oui		24	43	\N
57258	2	oui		24	44	\N
57259	3	oui		24	45	\N
57260	3	oui		24	46	\N
57261	1	oui	Besoin de remplacer les corbeilles	24	47	["/static/uploads/b0f709b9-e70e-4298-b061-322cc7ae867e.jpg", "/static/uploads/972ac419-0d81-4728-b416-d5619d0655cd.jpg"]
57262	3	oui	La machine à café Révolution présente une mauvaise qualité de café. Un ticket de support a été envoyé.	24	48	\N
57263	3	oui	Besoin dune camera Positionné au niveau des escaliers.	24	49	\N
57264	10	non		24	50	\N
57265	0	oui	Boîte alimentaire fissurée, à remplacer.\nEt une autre qui a besoin de couvercle.	24	51	["/static/uploads/987ec96f-6bc2-4276-a2db-e598cea9c787.jpg", "/static/uploads/d298657e-cb32-4aff-aca7-0c7e75448fd4.jpg"]
57266	3	non		24	52	\N
57267	3	oui		24	53	\N
57268	3	oui		24	54	\N
57269	2	oui		24	55	\N
57270	5	oui		24	56	\N
57271	3	oui		24	57	\N
57272	6	oui		24	58	\N
57273	2	oui		24	59	\N
57274	2	oui		24	60	\N
57275	2	oui		24	61	\N
57276	3	oui		24	62	\N
57277	1	oui		24	63	\N
57278	5	oui		24	64	\N
57279	2	oui		24	65	\N
57280	2	oui		24	66	\N
57281	4	oui		24	67	["/static/uploads/3d0527fc-def6-4cde-a024-1630fb22e033.jpg"]
57282	4	oui		24	68	\N
57283	2	non	Trois ampoules ne fonctionnent pas et doivent être remplacées.	24	69	["/static/uploads/5768805c-12a6-4485-bc66-651aa9d08e13.jpg", "/static/uploads/8c4cee40-5404-4f50-9eed-60e1232be475.jpg", "/static/uploads/f0f08af1-e6b2-4b68-8eb8-663246332f7a.jpg"]
57284	2	oui		24	70	\N
57285	10	oui		24	71	\N
57286	4	oui		24	73	\N
57287	2	oui		24	74	\N
57288	1	oui		24	75	\N
57289	1	oui		24	76	\N
57290	3	oui		24	77	["/static/uploads/bb809486-08d8-47e1-90f3-15bceb002d00.jpg"]
57291	0	non	Le personnel doit recevoir sa carte sanitaire.	24	78	\N
62392	0	non	Plantes mal entretenues.\nDétérioration du vinyle ; il est préférable de le poser à l’intérieur.	26	26	["/static/uploads/667a3f14-2919-4bdb-84bb-a8ea4a333aa0.jpg", "/static/uploads/c7acbc36-324f-4c13-b4eb-20098ed3562c.jpg", "/static/uploads/2db4d350-1651-4769-96ec-9602311a3fc6.jpg"]
62393	3	oui		26	27	\N
62394	2	oui		26	28	\N
62395	2	oui		26	29	\N
62396	3	oui		26	30	\N
62397	3	oui		26	31	\N
62398	1	oui		26	32	\N
62399	1	oui		26	33	\N
62400	1	oui		26	34	\N
62401	4	oui		26	35	\N
62402	3	oui		26	36	\N
62403	0	n/a		26	38	\N
62404	1	oui		26	39	\N
62405	5	oui		26	40	\N
62406	5	oui		26	41	\N
62407	2	oui		26	42	\N
62408	2	oui		26	43	\N
62409	2	oui		26	44	\N
62410	3	oui		26	45	\N
62411	3	oui		26	46	\N
62412	1	oui		26	47	\N
62413	3	oui		26	48	\N
62414	3	oui		26	49	\N
62415	10	non	Mango sauce retour a mouhamadia	26	50	\N
62416	10	non		26	51	\N
62417	3	non		26	52	\N
62418	3	oui		26	53	\N
62419	3	oui		26	54	\N
62420	2	oui		26	55	\N
62421	5	oui		26	56	\N
62422	3	oui		26	57	\N
62423	6	oui		26	58	\N
62424	2	oui		26	59	\N
62425	2	oui		26	60	\N
62426	2	oui		26	61	\N
62427	3	oui		26	62	\N
62428	1	oui		26	63	\N
62429	5	oui		26	64	\N
62430	2	oui		26	65	\N
62431	2	oui	46ppm	26	66	["/static/uploads/deaeb7c3-d1ae-4a06-b0e2-862c86c9787a.jpg"]
62432	4	oui		26	67	\N
62433	4	oui		26	68	\N
62434	2	non		26	69	\N
62435	2	oui		26	70	\N
62436	10	oui		26	71	\N
62437	4	oui		26	73	\N
62438	2	oui		26	74	\N
62439	1	oui		26	75	\N
62440	1	oui		26	76	\N
62441	0	non	Pest control non disponible	26	77	\N
62442	0	non	Carte sanitaire non disponible : nécessité de remettre les cartes sanitaires au staff.	26	78	\N
74547	2	oui		28	44	\N
74548	3	oui		28	45	\N
74549	3	oui		28	46	\N
74550	1	oui		28	47	\N
74551	3	oui		28	48	\N
74552	3	oui		28	49	\N
74553	10	non		28	50	\N
74554	10	non		28	51	\N
74555	3	non		28	52	\N
74556	3	oui		28	53	\N
74557	3	oui		28	54	\N
74558	2	oui		28	55	\N
74559	5	oui		28	56	\N
74560	3	oui		28	57	\N
74561	6	oui		28	58	\N
74562	2	oui		28	59	\N
74563	2	oui		28	60	\N
74564	2	oui		28	61	\N
74565	3	oui		28	62	\N
74566	1	oui		28	63	\N
74567	5	oui		28	64	\N
129916	0	non	plante mal entretenue	42	26	["/static/uploads/7ae2f83a-49f6-4dd2-a413-50e5b02f5f9e.jpg"]
129917	3	oui		42	27	\N
129918	2	oui		42	28	\N
129919	2	oui		42	29	\N
129920	3	oui		42	30	\N
129921	3	oui		42	31	\N
129922	1	oui		42	32	\N
129923	1	oui		42	33	\N
129924	1	oui		42	34	\N
129925	4	oui		42	35	["/static/uploads/9f38f9a2-02c0-4b5d-9ef9-aad5a649a961.jpg", "/static/uploads/dce179da-caaf-40ad-9707-837187b4c24f.jpg"]
129926	0	non	QR code Google avis ne fonctionne pas	42	36	["/static/uploads/9c0b6c86-f82b-42e9-8422-6aa0f786ebc1.jpg"]
129927	4	oui		42	38	\N
129928	1	oui		42	39	\N
129929	5	oui		42	40	["/static/uploads/3228d29e-4f1f-4c57-bfc1-5d705c045b73.jpg", "/static/uploads/985ab93c-df43-4718-91bc-d1781b7ee897.jpg"]
129930	5	oui		42	41	\N
129931	2	oui		42	42	\N
129932	2	oui		42	43	\N
129933	2	oui		42	44	\N
129934	3	oui		42	45	\N
129935	3	oui		42	46	\N
129936	0	non		42	47	["/static/uploads/b48500b4-2b3a-473c-a657-8d12d4493d41.jpg", "/static/uploads/9b577a99-902f-49b7-aad7-114a8217e5ef.jpg"]
129937	0	non	Blender en panne.\nLe cadran d’affichage ne fonctionne pas	42	48	["/static/uploads/c19bd005-4e2a-41de-b756-7e1f246f3861.jpg", "/static/uploads/1512bebc-7155-479a-9762-8150bbf7d127.jpg"]
129938	3	oui		42	49	\N
129939	10	non		42	50	\N
129940	10	non		42	51	\N
129941	3	non		42	52	\N
129942	3	oui		42	53	\N
129943	3	oui		42	54	\N
129944	2	oui		42	55	\N
129945	5	oui		42	56	\N
129946	3	oui		42	57	\N
129947	6	oui		42	58	\N
129948	2	oui		42	59	\N
129949	2	oui		42	60	\N
129950	2	oui		42	61	\N
129951	3	oui		42	62	\N
129952	1	oui		42	63	\N
129953	5	oui		42	64	\N
129954	2	oui		42	65	\N
129955	2	oui		42	66	\N
129956	4	oui		42	67	\N
129957	4	oui		42	68	\N
129958	2	non		42	69	\N
129959	2	oui		42	70	\N
129960	10	oui		42	71	\N
129961	4	oui		42	73	\N
129962	2	oui		42	74	\N
129963	1	oui		42	75	\N
129964	1	oui		42	76	\N
129965	3	oui		42	77	["/static/uploads/8f2aa5e0-131a-4e1c-ab05-e989df0f0c7e.jpg"]
129966	0	non	Le staff na pas de carte sanitaire 	42	78	\N
138858	2	oui		45	44	\N
138859	3	oui		45	45	\N
138860	3	oui		45	46	\N
138861	1	oui		45	47	\N
138862	3	oui		45	48	\N
138863	3	oui		45	49	\N
138864	10	non		45	50	\N
138865	10	non		45	51	\N
138866	3	non		45	52	\N
138867	3	oui		45	53	\N
138868	3	oui		45	54	\N
138869	2	oui		45	55	\N
138870	0	non	Manque de badges nominatifs : l’une l’a perdu, l’autre a informé Sara qu’il n’était plus fonctionnel.	45	56	\N
138871	3	oui		45	57	\N
138872	6	oui		45	58	\N
138873	2	oui		45	59	\N
138874	2	oui		45	60	\N
138875	2	oui		45	61	\N
138876	3	oui		45	62	\N
138877	1	oui		45	63	\N
138878	5	oui		45	64	\N
138879	2	oui		45	65	\N
138880	2	oui		45	66	\N
138881	4	oui		45	67	\N
138882	4	oui		45	68	\N
138883	2	non	plusieurs ampoules grillées  (ticket support ouvert)	45	69	\N
138884	2	oui		45	70	\N
138885	10	oui		45	71	\N
138886	4	oui		45	73	\N
138887	2	oui		45	74	\N
138888	1	oui		45	75	\N
138889	1	oui		45	76	\N
138890	3	oui		45	77	["/static/uploads/cb71d40b-994d-40d1-9f9c-234f97c3ed62.jpg"]
138891	0	non	le staff na pas de carte sanitaire	45	78	\N
138892	0	\N		46	26	\N
138893	0	\N		46	27	\N
138894	0	\N		46	28	\N
138895	0	\N		46	29	\N
138896	0	\N		46	30	\N
138897	0	\N		46	31	\N
138898	0	\N		46	32	\N
138899	0	\N		46	33	\N
138900	0	\N		46	34	\N
138901	0	\N		46	35	\N
138902	0	\N		46	36	\N
138903	0	\N		46	38	\N
138904	0	\N		46	39	\N
138905	0	\N		46	40	\N
138906	0	\N		46	41	\N
138907	0	\N		46	42	\N
138908	0	\N		46	43	\N
138909	0	\N		46	44	\N
138910	0	\N		46	45	\N
138911	0	\N		46	46	\N
138912	0	\N		46	47	\N
138913	0	\N		46	48	\N
138914	0	\N		46	49	\N
138915	0	\N		46	50	\N
138916	0	\N		46	51	\N
138917	0	\N		46	52	\N
138918	0	\N		46	53	\N
138919	0	\N		46	54	\N
138920	0	\N		46	55	\N
138921	0	\N		46	56	\N
138922	0	\N		46	57	\N
138923	0	\N		46	58	\N
138924	0	\N		46	59	\N
138925	0	\N		46	60	\N
138926	0	\N		46	61	\N
138927	0	\N		46	62	\N
138928	0	\N		46	63	\N
138929	0	\N		46	64	\N
88249	3	oui		30	26	\N
88250	0	non	La peinture présente des défauts et nécessite une remise en état	30	27	["/static/uploads/f858d5f5-9f68-4836-af81-4b9e2a163b32.jpg", "/static/uploads/94a1ab42-285e-4f3e-9ce9-bb8bb3702a5f.jpg", "/static/uploads/de39ecfa-9147-4292-9731-46e7299a514f.jpg", "/static/uploads/064e4b2d-3ac5-4b3e-beb0-14de4e040db7.jpg", "/static/uploads/37a17a39-5dae-4be0-bb77-523f3bf8ba97.jpg", "/static/uploads/76d07301-7e6b-4ecf-816d-8ce43c290535.jpg", "/static/uploads/a7bf6889-b6e7-4dfa-9e0d-33b70ec9621b.jpg", "/static/uploads/da8cee59-acd0-49fe-a600-0d5bab201d04.jpg"]
88251	2	oui		30	28	\N
88252	2	oui		30	29	\N
88253	3	oui		30	30	\N
88254	3	oui		30	31	\N
88255	1	oui		30	32	\N
88256	1	oui		30	33	\N
88257	1	oui		30	34	\N
88258	4	oui		30	35	["/static/uploads/88e0da76-f672-458b-b78e-f857117fb9d7.jpg"]
88259	3	oui		30	36	\N
88260	4	oui		30	38	\N
88261	0	non	Besoin d’un balai et d’un manche à balai\nD’un seau d'eau	30	39	\N
88262	5	oui		30	40	["/static/uploads/029c9e77-a0a8-4bfe-9b76-bafe5c2893b0.jpg", "/static/uploads/6a024a3c-fafe-4502-bd21-0a1292f05599.jpg", "/static/uploads/c2861008-ae7b-4f56-a677-82d50dc0ebb1.jpg"]
88263	0	non	Preparation non etiquetés	30	41	["/static/uploads/8db7479c-3993-437f-9098-8a7a9c7c4abd.jpg"]
88264	2	oui		30	42	\N
88265	2	oui		30	43	\N
88266	2	oui		30	44	\N
88267	3	oui		30	45	\N
88268	3	oui		30	46	\N
88269	0	non	Les poubelles ne sont pas fermées et sont pleines.	30	47	["/static/uploads/e20a7839-b657-47d6-8841-f57e50724bac.jpg", "/static/uploads/8a05f06d-9d7e-42ee-870f-b61b7d899866.jpg", "/static/uploads/16812d54-c589-47e2-9d02-7cdcace114c5.jpg"]
88270	3	oui		30	48	\N
88271	3	oui		30	49	\N
88272	10	non		30	50	\N
88273	10	non		30	51	\N
88274	3	non		30	52	\N
88275	0	non	Plusieurs sauces ne sont pas bien positionnées selon le FIFO.\nUne sauce white est ouverte avec une DLC supérieure à une autre sauce déjà en stock.	30	53	["/static/uploads/d11c801f-d1ee-4d72-85dc-23c3004ed2b9.jpg", "/static/uploads/24b26573-f39f-4ae8-9fd3-830ed489979e.jpg", "/static/uploads/7b93ac44-d776-455d-9899-9fb5380b4376.jpg"]
88276	3	oui		30	54	\N
88277	2	oui		30	55	\N
88278	5	oui		30	56	\N
88279	3	oui		30	57	\N
88280	6	oui		30	58	\N
88281	2	oui		30	59	\N
88282	2	oui		30	60	\N
88283	2	oui		30	61	\N
88284	3	oui		30	62	\N
88285	1	oui		30	63	\N
88286	5	oui		30	64	\N
88287	2	oui		30	65	\N
88288	2	oui		30	66	\N
88289	4	oui		30	67	\N
88290	4	oui		30	68	\N
88291	2	non		30	69	\N
88292	2	oui		30	70	\N
88293	10	oui		30	71	\N
88294	4	oui		30	73	\N
88295	2	oui		30	74	\N
88296	1	oui		30	75	\N
88297	1	oui		30	76	\N
88298	3	oui		30	77	["/static/uploads/bac547d3-5c8d-4433-92cd-a183ea4d382f.jpg"]
88299	0	non	Le staff doit recevoir leur carte sanitaire.	30	78	\N
138930	0	\N		46	65	\N
138931	0	\N		46	66	\N
138932	0	\N		46	67	\N
138933	0	\N		46	68	\N
138934	0	\N		46	69	\N
138935	0	\N		46	70	\N
138936	0	\N		46	71	\N
138937	0	\N		46	73	\N
138938	0	\N		46	74	\N
138939	0	\N		46	75	\N
138940	0	\N		46	76	\N
138941	0	\N		46	77	\N
138942	0	\N		46	78	\N
138943	0	\N		47	26	\N
138944	0	\N		47	27	\N
138945	0	\N		47	28	\N
138946	0	\N		47	29	\N
138947	0	\N		47	30	\N
138948	0	\N		47	31	\N
138949	0	\N		47	32	\N
138950	0	\N		47	33	\N
138951	0	\N		47	34	\N
138952	0	\N		47	35	\N
138953	0	\N		47	36	\N
138954	0	\N		47	38	\N
138955	0	\N		47	39	\N
138956	0	\N		47	40	\N
138957	0	\N		47	41	\N
138958	0	\N		47	42	\N
138959	0	\N		47	43	\N
138960	0	\N		47	44	\N
138961	0	\N		47	45	\N
138962	0	\N		47	46	\N
138963	0	\N		47	47	\N
138964	0	\N		47	48	\N
138965	0	\N		47	49	\N
68104	0	non	Plante mal entretenue\nVase fissuré\nchauffages d’extérieur\nBesoin de chaises\nBesoin de deux bombone a gaze pour les chauffage texterieur	27	26	["/static/uploads/acb3a574-fccf-4b76-9bef-57cec06670b3.jpg", "/static/uploads/6a108992-a6d6-4ac2-8e1e-c0f3d8cc4629.jpg", "/static/uploads/3816e200-430e-461c-ae8f-72634e091144.jpg"]
68105	3	oui		27	27	\N
68106	2	oui		27	28	\N
68107	2	oui		27	29	\N
68108	3	oui		27	30	\N
68109	3	oui		27	31	\N
68110	0	non	Problème d’amplificateur	27	32	["/static/uploads/1af79a72-4163-4f61-97e4-d76a2fdad2ed.jpg"]
68111	0	non	La climatisation ne fonctionne pas.	27	33	["/static/uploads/2ca3d3dc-22da-4631-9fe6-d0ae42482622.jpg"]
68112	1	oui		27	34	\N
68113	4	oui		27	35	["/static/uploads/31f243aa-ddae-46c9-a5c6-bbc390338fda.jpg"]
68114	3	oui		27	36	\N
68115	4	oui	Petit problème au niveau du bouton de la chasse d’eau : il est fonctionnel, mais mal posé.	27	38	["/static/uploads/3f5640d2-f12e-4e0d-a96c-7f21114b1f05.jpg"]
68116	1	oui	Manque de torchons pour le nettoyage\nBesoin d’un manche pour serpillière\nBesoin d’une serpillière (mop)\nBesoin de produit pour le sol	27	39	["/static/uploads/67eb59bf-ba39-4218-85eb-14f74d617fd5.jpg", "/static/uploads/3a3ac68e-882e-4fca-ad27-d5679104903e.jpg", "/static/uploads/39a32aef-908e-4e5c-8ae5-f30f1965d1f1.jpg"]
68117	5	oui		27	40	["/static/uploads/884706a8-7c32-4665-a6a5-606e5b5e0847.jpg", "/static/uploads/aead2d5a-1fb5-4022-9450-151d578057fe.jpg", "/static/uploads/fd59c167-97fd-4024-a195-1afad4b309b2.jpg"]
68118	5	oui		27	41	\N
68119	2	oui		27	42	\N
68120	2	oui		27	43	\N
68121	2	oui		27	44	\N
68122	3	oui		27	45	\N
68123	3	oui		27	46	\N
68124	1	oui		27	47	\N
68125	3	oui		27	48	\N
68126	3	oui		27	49	\N
68127	10	non		27	50	\N
68128	10	non		27	51	\N
68129	3	non		27	52	\N
68130	0	non	Le FIFO n’est pas respecté : plusieurs sacs de petit pain sont ouverts avec des dates différentes	27	53	["/static/uploads/9a0e846c-f581-4988-8f31-6646bb6d416b.jpg", "/static/uploads/c441921c-20b9-4b3f-9bca-c9988253ab48.jpg", "/static/uploads/b537a437-b103-4f2c-893a-437c29105fa8.jpg", "/static/uploads/c51d51b6-02c5-4dd4-b0c8-3db3b448b878.jpg"]
68131	3	oui		27	54	\N
68132	2	oui		27	55	["/static/uploads/890aac0f-4098-4eee-9312-784ad9d19f91.jpg"]
68133	5	oui		27	56	\N
68134	3	oui		27	57	\N
68135	6	oui		27	58	\N
68136	2	oui		27	59	\N
68137	2	oui		27	60	\N
68138	2	oui		27	61	\N
68139	3	oui		27	62	\N
68140	1	oui		27	63	\N
68141	5	oui		27	64	\N
68142	2	oui		27	65	\N
68143	2	oui	Ppm a 20	27	66	["/static/uploads/f5ad0950-5ebd-4b6d-9f85-973e049cbf22.jpg"]
68144	4	oui		27	67	["/static/uploads/ad2ad1bb-16cd-4cd3-af8e-a6fc111edddd.jpg"]
68145	4	oui		27	68	\N
68146	2	non		27	69	\N
68147	2	oui		27	70	\N
68148	10	oui		27	71	\N
68149	4	oui		27	73	\N
68150	2	oui		27	74	\N
68151	1	oui		27	75	\N
68152	1	oui		27	76	\N
68153	0	non	Pas de pest control depuis December 2025\nBesoin du passage du control 	27	77	\N
68154	0	non	Besoin de carte sanitaire pour le staff	27	78	\N
138966	0	\N		47	50	\N
138967	0	\N		47	51	\N
138968	0	\N		47	52	\N
138969	0	\N		47	53	\N
138970	0	\N		47	54	\N
138971	0	\N		47	55	\N
138972	0	\N		47	56	\N
138973	0	\N		47	57	\N
138974	0	\N		47	58	\N
138975	0	\N		47	59	\N
138976	0	\N		47	60	\N
138977	0	\N		47	61	\N
138978	0	\N		47	62	\N
138979	0	\N		47	63	\N
138980	0	\N		47	64	\N
138981	0	\N		47	65	\N
138982	0	\N		47	66	\N
138983	0	\N		47	67	\N
138984	0	\N		47	68	\N
138985	0	\N		47	69	\N
138986	0	\N		47	70	\N
138987	0	\N		47	71	\N
138988	0	\N		47	73	\N
138989	0	\N		47	74	\N
138990	0	\N		47	75	\N
138991	0	\N		47	76	\N
138992	0	\N		47	77	\N
138993	0	\N		47	78	\N
140204	0	\N		49	64	\N
140205	0	\N		49	65	\N
102019	0	non	Détérioration du vinyle ; il est préférable de le poser à l’intérieur	37	26	\N
102020	3	oui		37	27	\N
102021	2	oui		37	28	\N
102022	2	oui		37	29	\N
102023	3	oui		37	30	\N
102024	3	oui		37	31	\N
102025	1	oui		37	32	\N
102026	1	oui		37	33	\N
102027	1	oui		37	34	\N
102028	4	oui		37	35	\N
102029	3	oui		37	36	\N
102030	0	n/a		37	38	\N
102031	1	oui		37	39	\N
102032	5	oui		37	40	\N
102033	5	oui		37	41	\N
102034	2	oui		37	42	\N
102035	2	oui		37	43	\N
102036	2	oui		37	44	\N
102037	3	oui		37	45	\N
102038	3	oui		37	46	\N
102039	0	non	Être attentif au vidage des poubelles et les vider régulièrement.	37	47	\N
102040	3	oui	machine à café Révolution fait du bruit et a des fuites d’eau\nTicket ouvert	37	48	["/static/uploads/a1dc6fbe-66b9-45bf-830d-8dd6df36d7fa.jpg"]
102041	3	oui		37	49	\N
140206	0	\N		49	66	\N
140207	0	\N		49	67	\N
140208	0	\N		49	68	\N
140209	0	\N		49	69	\N
140210	0	\N		49	70	\N
140211	0	\N		49	71	\N
140212	0	\N		49	73	\N
140213	0	\N		49	74	\N
140214	0	\N		49	75	\N
140215	0	\N		49	76	\N
143329	0	non		48	26	["/static/uploads/8fa4304e-22fe-48e5-bc0c-03cd4762ed31.jpg", "/static/uploads/3c8b448a-7bcf-4ef6-9ddc-5d0c4f439ae5.jpg", "/static/uploads/28f83da7-a0a9-4ec7-9cbe-204d83d1171d.jpg", "/static/uploads/6450a58e-afaa-450e-8591-1f8c5cbf2415.jpg", "/static/uploads/a121904a-ad8b-47fe-9f61-d1386f41b452.jpg", "/static/uploads/b7f3e323-b99b-494f-800e-6f0b8d657863.jpg", "/static/uploads/f496b09c-ce37-4c78-9b75-aa49653c5889.jpg"]
143330	3	oui		48	27	\N
143331	0	non		48	28	\N
143332	2	oui		48	29	\N
143333	3	oui		48	30	\N
143334	3	oui		48	31	\N
143335	1	oui		48	32	\N
143336	1	oui		48	33	\N
143337	1	oui		48	34	\N
143338	4	oui		48	35	\N
143339	0	\N		48	36	\N
143340	0	\N		48	38	\N
143341	0	\N		48	39	\N
143342	0	\N		48	40	\N
143343	5	oui		48	41	\N
143344	2	oui		48	42	\N
143345	2	oui		48	43	\N
143346	2	oui		48	44	\N
143347	0	non		48	45	["/static/uploads/10f9b330-09aa-4181-961e-d901d1fadbaf.jpg"]
143348	3	oui		48	46	\N
143349	1	oui		48	47	\N
143350	0	non		48	48	["/static/uploads/fa85c7d2-a3c2-46a7-a776-4e39d84d34fd.jpg"]
143351	3	oui		48	49	\N
143352	10	non		48	50	\N
143353	10	non		48	51	\N
143354	3	non		48	52	\N
143355	3	oui		48	53	\N
143356	3	oui		48	54	\N
143357	2	oui		48	55	\N
143358	5	oui		48	56	\N
143359	3	oui		48	57	\N
143360	6	oui		48	58	\N
143361	2	oui		48	59	\N
143362	2	oui		48	60	\N
143363	2	oui		48	61	\N
143364	0	\N		48	62	\N
143365	0	\N		48	63	\N
143366	0	\N		48	64	\N
143367	0	\N		48	65	\N
143368	0	\N		48	66	\N
143369	0	\N		48	67	\N
143370	0	\N		48	68	\N
143371	0	\N		48	69	\N
143372	0	\N		48	70	\N
143373	0	\N		48	71	\N
143374	0	\N		48	73	\N
143375	0	\N		48	74	\N
143376	0	\N		48	75	\N
143377	0	\N		48	76	\N
143378	0	\N		48	77	\N
143379	0	\N		48	78	\N
140216	0	\N		49	77	\N
140217	0	\N		49	78	\N
74530	0	non	Surface non nettoyée\nUne chaise cassée	28	26	["/static/uploads/8091351f-4645-44c6-8d04-3aef621c768a.jpg", "/static/uploads/4d04799f-69ca-4b2c-a4e8-f2194f554c32.jpg"]
74531	3	oui		28	27	\N
74532	2	oui		28	28	\N
74533	2	oui		28	29	\N
74534	3	oui		28	30	\N
74535	3	oui		28	31	\N
74536	1	oui		28	32	\N
74537	1	oui		28	33	\N
74538	1	oui		28	34	\N
74539	4	oui		28	35	["/static/uploads/cf48eac2-53d4-4aa4-b3b3-63dac2d5e5fc.jpg"]
74540	3	oui		28	36	\N
74541	4	oui	Le bouton de la chasse d’eau est cassé\n	28	38	["/static/uploads/d7c1a436-2d60-4826-85a9-fcf4c865a7aa.jpg"]
74542	1	oui	Ticket ouverts pour:\nBesoin de Balai à serpillère et\nUne serpillère	28	39	\N
74543	5	oui	Date d'expiration 12/26	28	40	["/static/uploads/4e5e2d78-c0c4-4bc7-ae1d-cccd395eed4b.jpg", "/static/uploads/1ae39b71-95ab-44f2-882d-1388dd17caac.jpg", "/static/uploads/8b148470-2caa-4685-a008-dc67d75ab331.jpg"]
74544	5	oui		28	41	\N
74545	2	oui		28	42	\N
74546	2	oui		28	43	\N
144553	0	non	test test 	50	26	["/static/uploads/9f71aa20-be13-466c-a902-827f7cc1dd1f.jpg"]
144554	3	oui		50	27	\N
144555	2	oui		50	28	\N
144556	2	oui		50	29	\N
144557	3	oui		50	30	\N
84118	3	oui		29	26	\N
84119	3	oui		29	27	\N
84120	2	oui		29	28	\N
84121	2	oui		29	29	\N
84122	3	oui		29	30	\N
74568	2	oui		28	65	\N
74569	2	oui		28	66	\N
74570	4	oui		28	67	["/static/uploads/7c05ffc6-ab9f-4114-b8c6-aa59e8d53795.jpg"]
74571	4	oui		28	68	\N
74572	2	non		28	69	\N
74573	2	oui		28	70	\N
74574	10	oui		28	71	\N
74575	4	oui		28	73	\N
74576	2	oui		28	74	\N
74577	1	oui		28	75	\N
74578	1	oui		28	76	\N
74579	0	non	Besoin de rapport pest control derniers date du 12/1/2026	28	77	["/static/uploads/a2c06179-2100-449e-adbc-8d17af5ab7c4.jpg"]
74580	0	non	Staff na pas reçu de carte sanitaire 	28	78	\N
84123	3	oui		29	31	\N
84124	1	oui		29	32	\N
84125	1	oui		29	33	\N
84126	1	oui		29	34	\N
84127	4	oui		29	35	["/static/uploads/09dc3f65-7b57-48eb-b693-edd26c587ed8.jpg"]
84128	3	oui		29	36	\N
84129	4	oui	Petit problème au niveau de la lunette des toilettes	29	38	["/static/uploads/142c2b9e-1875-47d6-80bc-af915cee2d46.jpg"]
84130	1	oui	Besoin de \n*serpiere\n*Balai\n	29	39	\N
84131	5	oui	Trois extincteurs\nDate d'expiration:\n6/2026\nPrévoir le remplacement a la fin du dlc 6/26	29	40	["/static/uploads/0e525ae0-d8fe-44fa-837d-9e8a30c72ed9.jpg", "/static/uploads/790848f0-6524-414e-bc8f-f1cddc9d8c89.jpg", "/static/uploads/b37e3609-61d1-4aa7-9b34-b3e3643cd399.jpg"]
84132	0	non	Preparation matcha sans dlc	29	41	["/static/uploads/ec935740-5091-4a99-99bd-8f6e426be5b7.jpg"]
84133	2	oui		29	42	\N
84134	0	non	Manque de produits \nasepcol\nMilav n	29	43	["/static/uploads/3a197081-6915-4a4b-8f11-befdef4dab66.jpg"]
84135	2	oui		29	44	\N
84136	3	oui		29	45	\N
84137	3	oui		29	46	\N
84138	0	non	2 poubelles pleines .\n	29	47	["/static/uploads/30157a6d-6fe9-4c33-8d6d-983533225ce2.jpg"]
84139	3	oui		29	48	\N
84140	3	oui		29	49	\N
84141	10	non		29	50	\N
84142	10	non		29	51	\N
84143	3	non	Rupture de chocolat blanc, mais le staff l’a signalé.	29	52	\N
84144	3	oui		29	53	\N
84145	3	oui		29	54	\N
84146	2	oui		29	55	\N
84147	5	oui		29	56	\N
84148	3	oui		29	57	\N
84149	6	oui		29	58	\N
84150	2	oui		29	59	\N
84151	2	oui		29	60	\N
84152	2	oui		29	61	\N
84153	3	oui		29	62	\N
84154	1	oui		29	63	\N
84155	5	oui		29	64	\N
84156	2	oui		29	65	\N
84157	2	oui	104 ppm	29	66	["/static/uploads/70625341-2fb6-4023-bddc-f73a104fb8fe.jpg"]
84158	4	oui		29	67	\N
84159	4	oui		29	68	\N
84160	2	non		29	69	\N
84161	2	oui		29	70	\N
84162	10	oui		29	71	\N
84163	4	oui		29	73	\N
84164	2	oui		29	74	\N
84165	1	oui		29	75	\N
84166	1	oui	Un peu lent	29	76	\N
84167	3	oui		29	77	["/static/uploads/911961ba-cd74-49a3-8730-79f2b9c04ab3.jpg", "/static/uploads/4a856f86-ab10-4412-9aaf-b2d429a02169.jpg", "/static/uploads/205db1db-be4a-4f71-8ce4-84e848e3e5bc.jpg"]
84168	2	oui		29	78	\N
105334	3	oui		38	26	\N
105335	3	oui		38	27	\N
105336	2	oui		38	28	\N
105337	2	oui		38	29	\N
105338	3	oui		38	30	\N
105339	3	oui		38	31	\N
105340	1	oui		38	32	\N
105341	1	oui		38	33	\N
105342	1	oui		38	34	\N
105343	4	oui		38	35	\N
105344	3	oui		38	36	\N
105345	0	n/a		38	38	\N
105346	1	oui		38	39	\N
105347	5	oui		38	40	["/static/uploads/d0455818-7183-44a2-aa0c-545d84390acb.jpg", "/static/uploads/799f2ce4-7d26-43d5-9774-ded5c03d1d15.jpg"]
105348	0	non	Dark chocolate\nSauce.le DLC est dépassé, le produit n’est plus consommable.\nCookies : absence de label.\n	38	41	["/static/uploads/1cfa356c-1138-4fac-bda1-6b8406aae3f2.jpg", "/static/uploads/dec19ae2-b8e6-41e1-9fa3-97090371ccc5.jpg"]
105349	2	oui		38	42	\N
105350	2	oui		38	43	\N
105351	2	oui		38	44	\N
105352	3	oui		38	45	\N
105353	3	oui		38	46	\N
105354	1	oui		38	47	\N
105355	3	oui		38	48	\N
105356	3	oui		38	49	["/static/uploads/82196e95-ce67-4908-a257-4f53bd8d380c.jpg", "/static/uploads/daeb4a73-3dc6-43e9-8230-972b8082496f.jpg"]
105357	10	non		38	50	\N
105358	10	non		38	51	\N
105359	3	non		38	52	\N
105360	3	oui		38	53	\N
105361	3	oui		38	54	\N
105362	2	oui		38	55	\N
105363	0	non	ABDELMOUHAIMINE HARCHI : pas de badge nominatif ni de tablier.	38	56	\N
105364	3	oui		38	57	\N
105365	6	oui		38	58	\N
105366	2	oui		38	59	\N
105367	2	oui		38	60	\N
105368	2	oui		38	61	\N
105369	3	oui		38	62	\N
105370	1	oui		38	63	\N
105371	0	non	Dark chocolate\nSauce.le DLC est dépassé, le produit n’est plus consommable.	38	64	["/static/uploads/eac47090-f85b-4cc1-91f1-76d209728284.jpg"]
105372	2	oui		38	65	\N
105373	2	oui		38	66	\N
105374	4	oui		38	67	["/static/uploads/bc521edf-7b59-413f-b197-ee04de37fdb2.jpg"]
144558	3	oui		50	31	\N
144559	1	oui		50	32	\N
144560	1	oui		50	33	\N
144561	1	oui		50	34	\N
144562	4	oui		50	35	\N
144563	3	oui		50	36	\N
144564	4	oui		50	38	\N
144565	1	oui		50	39	\N
144566	5	oui		50	40	\N
144567	5	oui		50	41	\N
144568	2	oui		50	42	\N
144569	0	non		50	43	["/static/uploads/17e717a3-8961-4cc5-a73a-399c3502e17d.jpg", "/static/uploads/36ff8119-c4b2-4313-ac15-ed50c7c3d843.jpg", "/static/uploads/44990ce7-865e-46a5-a13a-6322b67b1c10.jpg"]
144570	2	oui		50	44	\N
144571	3	oui		50	45	\N
144572	0	n/a		50	46	\N
144573	1	oui		50	47	\N
144574	3	oui		50	48	\N
144575	3	oui		50	49	\N
144576	0	oui	test 	50	50	["/static/uploads/609c3e01-fd50-400a-be4e-fe03d6f1eb30.jpg"]
144577	0	n/a		50	51	\N
144578	3	non		50	52	\N
144579	3	oui		50	53	\N
144580	3	oui		50	54	\N
144581	2	oui		50	55	\N
144582	5	oui		50	56	\N
144583	3	oui		50	57	\N
144584	6	oui		50	58	\N
144585	2	oui		50	59	\N
144586	2	oui		50	60	\N
144587	2	oui		50	61	\N
144588	3	oui		50	62	\N
144589	1	oui		50	63	\N
144590	5	oui		50	64	\N
144591	2	oui		50	65	\N
144592	2	oui		50	66	\N
144593	4	oui		50	67	\N
144594	4	oui		50	68	\N
144595	2	non		50	69	\N
144596	2	oui		50	70	\N
144597	10	oui		50	71	\N
140167	3	oui		49	26	\N
125224	3	oui		41	26	\N
125225	3	oui		41	27	\N
125226	2	oui		41	28	\N
125227	2	oui		41	29	\N
125228	3	oui		41	30	\N
125229	3	oui		41	31	\N
125230	1	oui		41	32	\N
125231	1	oui		41	33	\N
125232	1	oui		41	34	\N
125233	4	oui		41	35	["/static/uploads/2163619a-e8fb-4dc6-8050-4c893850dbdf.jpg"]
105375	4	oui		38	68	\N
105376	2	non		38	69	\N
105377	2	oui		38	70	\N
105378	10	oui		38	71	\N
105379	4	oui		38	73	\N
105380	2	oui		38	74	\N
105381	1	oui		38	75	\N
105382	1	oui		38	76	\N
105383	3	oui		38	77	["/static/uploads/59f2af9e-f05d-4ca0-b0b8-bb5928934193.jpg"]
105384	0	non	Besoin de carte sanitaire du sraff	38	78	\N
125234	3	oui		41	36	\N
125235	4	oui		41	38	\N
125236	1	oui	Besoin de serpiere a mop	41	39	\N
140168	0	n/a		49	27	\N
140169	2	oui		49	28	\N
140170	0	non		49	29	["/static/uploads/d1c058bc-81f4-4b9c-a670-ffca65a2bdd8.jpg"]
140171	0	\N		49	30	\N
140172	0	\N		49	31	\N
140173	0	\N		49	32	\N
140174	0	\N		49	33	\N
140175	0	\N		49	34	\N
140176	0	\N		49	35	\N
140177	0	\N		49	36	\N
140178	0	\N		49	38	\N
140179	0	\N		49	39	\N
140180	0	\N		49	40	\N
140181	0	\N		49	41	\N
140182	0	\N		49	42	\N
140183	0	\N		49	43	\N
140184	0	\N		49	44	\N
140185	0	\N		49	45	\N
140186	0	\N		49	46	\N
140187	0	\N		49	47	\N
140188	0	\N		49	48	\N
140189	0	\N		49	49	\N
140190	0	\N		49	50	\N
140191	0	\N		49	51	\N
140192	0	\N		49	52	\N
140193	0	\N		49	53	\N
140194	0	\N		49	54	\N
140195	0	\N		49	55	\N
140196	0	\N		49	56	\N
140197	0	\N		49	57	\N
140198	0	\N		49	58	\N
140199	0	\N		49	59	\N
140200	0	\N		49	60	\N
140201	0	\N		49	61	\N
140202	0	\N		49	62	\N
140203	0	\N		49	63	\N
110128	3	oui		39	26	\N
110129	3	oui		39	27	\N
110130	2	oui		39	28	\N
110131	2	oui		39	29	\N
110132	3	oui		39	30	\N
110133	3	oui		39	31	\N
110134	1	oui		39	32	\N
110135	1	oui		39	33	\N
110136	1	oui		39	34	\N
110137	4	oui		39	35	["/static/uploads/26cef31b-581f-4549-acf6-cf6e2de7410c.jpg"]
110138	3	oui		39	36	\N
93706	0	n/a		31	26	\N
93707	0	n/a		31	27	\N
93708	2	oui		31	28	\N
93709	2	oui	Il y a un problème au niveau de la deuxième porte  difficulté à l’ouvrir et à la fermer.	31	29	["/static/uploads/1ea359d0-16ab-4857-93a6-f8c761b0a5ab.jpg"]
93710	3	oui		31	30	\N
93711	3	oui		31	31	\N
93712	1	oui		31	32	\N
93713	1	oui		31	33	\N
93714	1	oui		31	34	\N
93715	4	oui		31	35	["/static/uploads/454e8773-78d3-46d1-a44d-df2160906d34.jpg"]
93716	3	oui		31	36	\N
93717	0	n/a		31	38	\N
93718	1	oui		31	39	\N
93719	5	oui		31	40	["/static/uploads/81b36780-a846-44b6-95f3-f2ea5cc32c50.jpg"]
93720	5	oui		31	41	\N
93721	2	oui		31	42	\N
93722	2	oui		31	43	\N
93723	2	oui		31	44	\N
93724	3	oui		31	45	\N
93725	3	oui		31	46	\N
93726	1	oui		31	47	\N
93727	3	oui		31	48	\N
93728	3	oui		31	49	\N
93729	10	non		31	50	\N
93730	10	non		31	51	\N
93731	0	oui		31	52	\N
93732	3	oui		31	53	\N
93733	3	oui		31	54	\N
93734	2	oui		31	55	\N
93735	5	oui		31	56	\N
93736	3	oui		31	57	\N
93737	6	oui		31	58	\N
93738	2	oui		31	59	\N
93739	2	oui		31	60	\N
93740	2	oui		31	61	\N
93741	3	oui		31	62	\N
93742	1	oui		31	63	\N
93743	5	oui		31	64	\N
93744	2	oui		31	65	\N
93745	2	oui		31	66	\N
93746	4	oui		31	67	["/static/uploads/1913e497-e595-4926-bbbb-f84d840567f4.jpg"]
93747	4	oui		31	68	\N
93748	2	non		31	69	\N
93749	2	oui		31	70	\N
93750	10	oui		31	71	\N
93751	4	oui		31	73	\N
93752	2	oui		31	74	\N
93753	1	oui		31	75	\N
93754	1	oui		31	76	\N
93755	3	oui		31	77	["/static/uploads/adc5a4af-9aec-436b-a2bf-19c3c8e67142.jpg"]
93756	0	non	Besion de carte sanitaire pour le staff	31	78	\N
110139	0	n/a		39	38	\N
110140	1	oui	Besoin de femme de ménage 	39	39	\N
110141	5	oui		39	40	["/static/uploads/1edd6019-839f-4178-87ba-8789391d5b0e.jpg", "/static/uploads/816f10fe-d1b5-4c17-9a37-c859963bc437.jpg"]
110142	5	oui		39	41	\N
110143	2	oui		39	42	\N
110144	2	oui		39	43	\N
110145	2	oui		39	44	\N
110146	0	non	L’afficheur du réfrigérateur est hors service.	39	45	["/static/uploads/158c4c1c-e44d-4e45-b224-8e81e2018865.jpg"]
110147	3	oui		39	46	\N
110148	1	oui		39	47	\N
110149	3	oui		39	48	\N
110150	3	oui		39	49	\N
110151	10	non		39	50	\N
110152	10	non		39	51	\N
110153	3	non		39	52	\N
110154	3	oui		39	53	\N
110155	3	oui		39	54	\N
110156	2	oui		39	55	\N
110157	5	oui		39	56	\N
110158	3	oui		39	57	\N
110159	6	oui		39	58	\N
110160	2	oui		39	59	\N
110161	2	oui		39	60	\N
110162	2	oui		39	61	\N
110163	3	oui		39	62	\N
110164	1	oui		39	63	\N
110165	0	non	Pas de dlc sur la mango sauce 	39	64	["/static/uploads/10dad89d-0f5f-4bdb-be10-b13d9e26a328.jpg", "/static/uploads/2db2bfe8-7356-4e67-ba85-8ba26fba3c62.jpg"]
110166	2	oui		39	65	\N
110167	2	oui	55ppm	39	66	["/static/uploads/d0d1bd72-4e59-442f-91c9-59dae7cadb29.jpg"]
110168	4	oui		39	67	\N
110169	4	oui		39	68	\N
110170	2	non		39	69	\N
110171	2	oui		39	70	\N
110172	10	oui		39	71	\N
110173	4	oui		39	73	\N
110174	2	oui		39	74	\N
110175	1	oui		39	75	\N
110176	1	oui		39	76	\N
110177	3	oui		39	77	["/static/uploads/5e32d5f7-4e19-4e7c-8efb-6936255820ad.jpg"]
110178	0	non	Le personnel doit recevoir ses cartes sanitaires.	39	78	\N
117931	3	oui		40	26	\N
117932	3	oui		40	27	\N
117933	2	oui		40	28	\N
117934	2	oui		40	29	\N
117935	3	oui		40	30	\N
117936	3	oui		40	31	\N
117937	1	oui		40	32	\N
117938	1	oui		40	33	\N
117939	1	oui		40	34	\N
117940	4	oui		40	35	["/static/uploads/b8782005-265a-444a-b987-d73aeaff14cb.jpg"]
117941	3	oui		40	36	\N
117942	4	oui		40	38	\N
117943	1	oui		40	39	\N
117944	5	oui		40	40	["/static/uploads/be5afd31-6113-47e4-a580-b3be3b619c90.jpg", "/static/uploads/ea034ac2-7c74-4cca-b5fd-4a5440bce8bc.jpg", "/static/uploads/524b5407-45f4-4ccb-aaa0-87549e5f2517.jpg"]
117945	0	non	Plusieurs produits n’ont pas de DLC.\nLa machine à café n’est pas approvisionnée en café.	40	41	["/static/uploads/fe81514f-77e5-4032-aac7-a9b9ba2a6206.jpg", "/static/uploads/da55b346-1f8b-41dd-b89c-c513d90a21b2.jpg", "/static/uploads/46d233c3-0ea9-47e0-8e08-c887cb986c19.jpg", "/static/uploads/d5cc1284-d922-4566-8dc8-12d147f9f0c1.jpg", "/static/uploads/22712592-f1c5-4f2d-af22-64f0309c1ca8.jpg"]
117946	2	oui		40	42	\N
117947	2	oui		40	43	\N
117948	2	oui		40	44	\N
117949	3	oui		40	45	\N
117950	3	oui		40	46	\N
102042	10	non		37	50	\N
102043	10	non		37	51	\N
102044	3	non		37	52	\N
102045	0	non	Produit ouvert avec une DLC inférieure à celle du stock	37	53	["/static/uploads/c289a711-102a-4eb4-846f-af24cf871a28.jpg", "/static/uploads/b2a378b8-ba2a-4fde-9b2c-05cd1c597112.jpg", "/static/uploads/c2d8d5df-2c67-49ff-9d15-611a0c65f25f.jpg"]
102046	3	oui		37	54	\N
102047	2	oui		37	55	\N
102048	5	oui		37	56	\N
102049	3	oui		37	57	\N
102050	6	oui		37	58	\N
102051	2	oui		37	59	\N
102052	2	oui		37	60	\N
102053	2	oui		37	61	\N
102054	3	oui		37	62	\N
102055	1	oui		37	63	\N
102056	5	oui		37	64	\N
102057	2	oui		37	65	\N
102058	2	oui		37	66	\N
102059	4	oui		37	67	\N
102060	4	oui		37	68	\N
102061	2	non		37	69	\N
102062	2	oui		37	70	\N
102063	10	oui		37	71	\N
102064	4	oui		37	73	\N
102065	2	oui		37	74	\N
102066	1	oui		37	75	\N
102067	1	oui		37	76	\N
102068	3	oui		37	77	\N
102069	0	non	staff doit recevoir les cartes sanitaire	37	78	\N
117951	0	non		40	47	["/static/uploads/f4cefb74-da01-461a-b57d-fb1399d46d6f.jpg", "/static/uploads/0744b281-af3e-44dd-884d-41f6cdcf5b87.jpg"]
117952	3	oui		40	48	\N
117953	3	oui		40	49	\N
117954	10	non		40	50	\N
117955	10	non		40	51	\N
117956	3	non		40	52	\N
117957	3	oui		40	53	\N
117958	3	oui		40	54	\N
117959	2	oui		40	55	\N
117960	0	non	Ahmed \nHanane\nPas de badge nominatif 	40	56	\N
117961	3	oui		40	57	\N
117962	6	oui		40	58	\N
117963	2	oui		40	59	\N
117964	2	oui		40	60	\N
117965	2	oui		40	61	\N
117966	3	oui		40	62	\N
117967	1	oui		40	63	\N
117968	0	non	Plusieurs produits n’ont pas de DLC.	40	64	["/static/uploads/f6ddf616-b1eb-43ea-baad-1d7d80466660.jpg", "/static/uploads/a1e338a0-92f9-41ef-933b-122c5d3eeb1d.jpg", "/static/uploads/b60c6fa1-a09c-4e3d-85ac-6f92effc28f4.jpg", "/static/uploads/7157ed46-fe15-4482-9922-0ae6001e08ad.jpg"]
117969	2	oui		40	65	\N
117970	2	oui		40	66	\N
117971	4	oui		40	67	["/static/uploads/403c3981-029e-42d6-a035-559e65a8d845.jpg"]
117972	4	oui		40	68	\N
117973	2	non		40	69	\N
117974	2	oui		40	70	\N
117975	10	oui		40	71	\N
117976	4	oui		40	73	\N
117977	2	oui		40	74	\N
117978	1	oui		40	75	\N
117979	1	oui		40	76	\N
117980	3	oui	Le dernier est disponible	40	77	["/static/uploads/037d42a8-40c9-4087-b94a-46ae3baf7eae.jpg"]
117981	0	non	Besoin de carte sanitaire pour le staff	40	78	\N
138841	3	oui		45	26	\N
138842	3	oui		45	27	\N
138843	2	oui		45	28	\N
138844	2	oui		45	29	\N
138845	3	oui		45	30	\N
138846	3	oui		45	31	\N
138847	1	oui		45	32	\N
138848	1	oui		45	33	\N
138849	1	oui		45	34	\N
138850	4	oui		45	35	\N
138851	3	oui		45	36	\N
138852	4	oui		45	38	\N
138853	1	oui		45	39	\N
138854	5	oui		45	40	["/static/uploads/831c09a7-5073-4cd2-9509-c07ffdd78c6b.jpg", "/static/uploads/b4031701-ecee-4cca-8f99-77b86428b723.jpg", "/static/uploads/af9a35a0-01c4-4a28-b0d2-61c76778063b.jpg"]
138855	0	non	Préparation matcha non étiquette 	45	41	\N
138856	2	oui		45	42	\N
138857	2	oui		45	43	\N
125237	5	oui		41	40	["/static/uploads/c9612426-e8bf-440a-8a96-fdc4c9d39bcc.jpg", "/static/uploads/78f989c6-2e14-4895-b1e4-c11eaec62674.jpg", "/static/uploads/b134eda9-7058-4d78-ba82-336d043d3c4e.jpg", "/static/uploads/89dc2b3d-34a2-4e3b-95ae-ba9cff388827.jpg"]
125238	0	non	sirop sans dlc	41	41	["/static/uploads/e0357887-7c4c-4ecf-88a4-adbd51dbe65f.jpg", "/static/uploads/c74720cf-9a5e-4984-8aec-8964f8da8cbe.jpg"]
125239	2	oui		41	42	["/static/uploads/27a7d73a-e20f-445b-8a2f-de5d57f36de1.jpg"]
125240	2	oui		41	43	\N
125241	2	oui		41	44	\N
125242	3	oui		41	45	\N
125243	3	oui		41	46	\N
125244	0	non		41	47	["/static/uploads/f8803f74-d89b-415a-9728-1faf3028b4c2.jpg"]
125245	3	oui		41	48	\N
125246	3	oui		41	49	\N
125247	10	non		41	50	\N
125248	10	non		41	51	\N
125249	3	non		41	52	\N
125250	3	oui		41	53	\N
125251	3	oui		41	54	\N
125252	2	oui		41	55	\N
125253	5	oui		41	56	\N
125254	3	oui		41	57	\N
125255	6	oui		41	58	\N
125256	2	oui		41	59	\N
125257	2	oui		41	60	\N
125258	2	oui		41	61	\N
125259	3	oui		41	62	\N
125260	1	oui		41	63	\N
125261	0	non	Sirop sans dlc	41	64	["/static/uploads/a33af718-f7b6-4642-9021-17a67554026d.jpg", "/static/uploads/4a1eb37a-cb6e-49f6-a132-1aafd13015c4.jpg"]
125262	0	non	Waste non envoyé	41	65	["/static/uploads/1426a056-b75b-4d69-9836-b0ce47df14f8.jpg"]
125263	2	oui		41	66	\N
125264	4	oui		41	67	\N
125265	4	oui		41	68	\N
125266	0	oui	Ampoule anti insecte grillée\nticket ouvert	41	69	\N
125267	2	oui		41	70	\N
125268	10	oui		41	71	\N
125269	4	oui		41	73	\N
125270	2	oui		41	74	\N
125271	1	oui		41	75	\N
125272	1	oui		41	76	\N
125273	3	oui		41	77	["/static/uploads/c49bb19e-5030-45c8-af50-beba3e4f4c56.jpg"]
125274	0	non	pas de carte sanitaire \npas d’autorisation du magasin , elle doit être disponible sur place 	41	78	\N
144598	4	oui		50	73	\N
144599	2	oui		50	74	\N
144600	1	oui		50	75	\N
144601	1	oui		50	76	\N
144602	3	oui		50	77	\N
144603	2	oui		50	78	\N
\.


--
-- Data for Name: audit_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_categories (id, name, description, icon, display_order) FROM stdin;
9	 Personnel & Connaissance	\N	🧑‍🍳	4
10	Maintenance & Matériel	\N	🛠️ 	5
7	Zone Comptoir	\N	🧾	2
6	Zone client & ambiance	\N	👥✨	1
5	Zone extérieure : terrasse, enseigne, plantes	\N	🌿🏪	0
8	Zone Stock	\N	📦	3
11	Gestion / Système	\N	💻⚙️	6
\.


--
-- Data for Name: audit_questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_questions (id, text, weight, category_id, correct_answer, na_score, display_order) FROM stdin;
52	Y'a-t-il une Rupture d'un ou plusieurs articles de manière NON justifié ? 	3	8	non	0	3
53	Le principe FEFO (First Expiry, First Out) est-il respecté ?	3	8	oui	0	4
54	Livraison vérifiée à réception (quantité, qualité, température).	3	8	oui	0	5
55	Produits chimique séparés des produits alimentaires.	2	8	oui	0	6
1	Les surfaces de travail sont propres et désinfectées	2	\N	oui	0	1
2	Les équipements sont en bon état de fonctionnement	1	\N	oui	0	2
11	Les commandes sont prises avec précision	2	\N	oui	0	11
78	Carte Sanitaire, Carte de travaille, Autorisation du magasin disponible.	2	11	oui	0	78
76	Système Odoo / POS/KDS à jour (Produits, Prix, Promotions).	1	11	oui	0	76
74	Caisse fonctionnelle avec fond de monnaie suffisant.\n	2	11	oui	0	74
61	Sait répondre aux questions sur les promotions / Produits en cours.	2	9	oui	0	61
66	Est-ce que la valeur du TDS est égale ou inférieure à (130 ppm) ?	2	10	oui	0	66
49	La zone de stockage est-elle propre, bien organisée et correctement éclairée ?\n	3	8	oui	0	0
3	Le personnel porte des vêtements propres et appropriés	2	\N	oui	0	3
4	Les produits alimentaires sont stockés à la bonne température	3	\N	oui	0	4
5	Les frigos et congélateurs sont propres, organisés avec thermomètre visible	2	\N	oui	0	5
6	Absence de produits périmés en stock ou en zone de préparation	3	\N	oui	0	6
7	Tous les produits sont bien emballés et stockés	1	\N	oui	0	7
8	Les poubelles sont fermées, propres et vidées	1	\N	oui	0	8
9	Le principe du FIFO (First In, First Out) est bien appliqué	2	\N	oui	0	9
10	L'accueil client est chaleureux et professionnel	3	\N	oui	0	10
12	Le temps d'attente est raisonnable	2	\N	oui	0	12
13	Le personnel connaît bien le menu et peut conseiller	2	\N	oui	0	13
14	Les réclamations sont gérées avec professionnalisme	3	\N	oui	0	14
15	Les boissons sont préparées selon les standards	3	\N	oui	0	15
16	La température des boissons est correcte	2	\N	oui	0	16
17	La présentation des produits est soignée	2	\N	oui	0	17
18	Les ingrédients utilisés sont frais et de qualité	3	\N	oui	0	18
19	Les portions respectent les standards établis	2	\N	oui	0	19
20	Le local est propre et bien rangé	2	\N	oui	0	20
21	Les tables et chaises sont propres	1	\N	oui	0	21
22	Les toilettes sont propres et approvisionnées	2	\N	oui	0	22
23	L'éclairage est adéquat	1	\N	oui	0	23
24	La musique d'ambiance est appropriée	1	\N	oui	0	24
25	La température du local est confortable	1	\N	oui	0	25
39	Tous les outils de nettoyage sont disponibles (raclette, vaporisateur, seau, brosse, ramasse-amigo).\n	1	6	oui	0	39
42	Planning de nettoyage quotidien et hebdomadaire affiché et suivi.\n	2	7	oui	0	42
70	Est-ce que les équipements du store fonctionnent correctement, sont propres et bien entretenus ?\n	2	10	oui	0	70
41	Zone de préparation propre et désinfectée, tous les produits alimentaire stockés et étiquetés.	5	7	oui	0	41
43	Tous les produits chimiques sont disponibles et correctement stockés.\n	2	7	oui	0	43
48	Est-ce que tous les équipements du comptoir fonctionnent correctement et sont bien nettoyés\n	3	7	oui	0	48
58	Planning de gestion du poste respecté.\n	6	9	oui	0	58
56	Uniformes complets propres, prénom visible, conformes à la charte de la marque.	5	9	oui	0	56
67	Tickets support créés pour toutes maintenance.	4	10	oui	0	67
50	Y a-t-il des produits périmés en stock ?\n	10	8	non	0	1
75	TPE fonctionnel, Tickets disponibles.	1	11	oui	0	75
36	Tous les outils marketing sont actualisés QR code du Wi-Fi et celui de Google Avis sont présents et fonctionnels.	3	6	oui	0	36
38	Toilettes propres, Savon et papier essuie-mains disponibles.	4	6	oui	0	38
40	Les extincteurs sont disponibles, Avec une date d’expiration valide et correctement accrochés.	5	6	oui	0	40
59	Les équipiers utilisent leur propre bracelet pour encaisser dans le système.	2	9	oui	0	59
57	Est-ce que les Clients sont accueilli correctement ? (Bonjour Bienvenue / Orientation pour commande).	3	9	oui	0	57
51	Y a-t-il des produits mal emballés ?\n	10	8	non	0	2
60	Le staff connaît les recettes, les allergènes et les options (Milk, syrup, etc).	2	9	oui	0	60
68	Machines à café nettoyées et fonctionnelles.	4	10	oui	0	68
69	Ampoule grillée / prise cassée / câble apparent.	2	10	non	0	69
63	Température des boissons chaudes / Froides conforme.\n	1	9	oui	0	63
65	Stratégie d’upselling, Gestion des déchets.\n	2	9	oui	0	65
64	Traçabilité des produits ouverts.	5	9	oui	0	64
62	Boissons conformes aux standards visuels (Look, Topping, Dosage, Gout).	3	9	oui	0	62
46	Lavage des mains respecté (fréquence, technique, savon) chaque 20 min.	3	7	oui	0	46
47	Poubelles fermées, Propres et vidées régulièrement.	1	7	oui	0	47
27	Peinture: Couleurs appropriées, Pas d'écaillage ni de décoloration.	3	5	oui	0	1
44	Plans de travail nettoyés entre chaque usage.	2	7	oui	0	44
30	Sols propres, Pas de déchets ni liquides visibles.	3	6	oui	0	30
31	Tables et chaises propres, Bien positionnées et équilibrées.	3	6	oui	0	31
32	Musique de fond conforme aux playlists / Ambiance calme.	1	6	oui	0	32
33	Aération / Clim / Chauffage fonctionnels.	1	6	oui	0	33
34	Odeur agréable (Pas de cuisson excessive ou de déchets).	1	6	oui	0	34
35	Présentation des viennoiseries et snacks conforme, Présentoir propre et bien garni.	4	6	oui	0	35
45	Réfrigérateurs propres, Organisés et munis d'un thermomètre visible indiquant une température entre 2 et 8 °C.	3	7	oui	0	45
28	Éclairage/Signalisation: Fonctionnels, Bien orientés, Minuterie Réglée correctement.	2	5	oui	0	2
29	Portes: Fonctionnement adéquat.	2	5	oui	0	3
71	Fond De Caisse, Glovo, TPE sont correcte ? 	10	11	oui	0	71
73	Checklists mises à jour et complétées ? 	4	11	oui	0	73
77	Les rapports de contrôle des nuisibles (Pest Control) des 3 derniers mois sont disponibles.\n	3	11	oui	0	77
26	Structure: Pas de pourriture, Pas de trous, Surface nettoyée, Vitres du patio propres, Plantes bien entretenues.	3	5	oui	0	0
\.


--
-- Data for Name: audits; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audits (id, created_at, updated_at, score, coffee_id, auditor_id, shift, staff_present, actions_correctives, training_needs, purchases, photo_url, status, date) FROM stdin;
29	2026-04-03 10:21:56.425744+00	2026-04-04 07:55:04.554797+00	94.97	5	8	AM	Iman elmakhloufi\nYassir elbakalli\nAli Belarus\nWefaa moubachir	Il faut réparer la lunette des toilettes.\nIl faut être plus attentif au vidage des poubelles.\n\n	Greeter ok\nBarista ok\nsuper gloo ok\nLa Presonne en Formation ok\n	Asepcol\nMilav n\nSavon a main\nSerpiere \nBalai et manche a balai\nWith chocolate sauce \n	["/static/uploads/3c62ff19-72fc-4df7-a0cb-5f4be3a054f4.jpg"]	COMPLETED	2026-04-03 06:21:00+00
40	2026-04-08 14:15:43.705089+00	2026-04-09 16:41:59.335518+00	88.68	13	8	AM	Ahmad ABOUATMANE\nHanane BOUASRIA\nAbdelhakim \n	Être attentif au nettoyage des poubelles régulièrement tout au long du service.\nFaire attention à noter toutes les DLC des produits ouverts.\nVeiller à approvisionner toutes les machines à café en café.\nRemettre les cartes sanitaires au staff.	Greeter ok \nbarista ok\nSuper gloo ok		["/static/uploads/8e305534-ff3b-48ce-af72-bc69754f12f1.jpg"]	COMPLETED	2026-04-04 07:11:00+00
37	2026-04-07 10:31:33.872937+00	2026-04-08 11:57:57.555909+00	94.19	2	8	PM	BEDERDINNE FAKRAOUI	Détérioration du vinyle ; il est préférable de le poser à l’intérieur\nÊtre attentif au vidage des poubelles et les vider régulièrement.\nEtre \nÊtre plus attentif aux DLC des produits.\nstaff doit recevoir les cartes sanitaire\n\n	greeter ok\nbarista ok\nsuppergloo ok	Réparer la machine à café Coffee Revolution : fuite d’eau et machine bruyante.	\N	COMPLETED	2026-04-06 11:31:00+00
26	2026-03-25 15:26:52.348448+00	2026-03-27 08:36:27.06724+00	94.84	2	8	PM	Badredine fekraoui\nKhaoula faouzi\nYasir lamsalak\nAymane bellane 	Besoin de nettoyer les vases des plantes.	Staff ok \nSuper gloo 👍\nGreeter 👍\nBarista 👍	Besoin de boîtes sanitaires.	\N	COMPLETED	2026-03-25 14:26:00+00
24	2026-03-24 13:48:45.585701+00	2026-03-25 11:35:21.195868+00	92.45	1	8	AM	Aymane el hajjaji	Maintenance\nTrois boîtes alimentaires doivent être remplacées. \nTrois ampoules a \nremplacées.\nMachine à café revolution à réparer.\n	Staff\nGreeter ok\nBarista ok\nSupergloo ok\n		\N	COMPLETED	2026-03-24 13:48:45.585701+00
49	2026-04-17 10:50:24.788845+00	2026-04-17 10:52:39.968414+00	3.21	10	9	AM	salim - hamza				["/static/uploads/a0ad01e6-6874-434b-9e21-113579b31a24.jpg"]	IN_PROGRESS	2026-04-17 06:50:00+00
50	2026-04-17 11:22:59.741856+00	2026-04-17 11:32:19.872757+00	89.73	10	11	AM	salma - imad 	test test 			["/static/uploads/36d54d01-39c8-43dd-831c-e1b7b83dc1ab.jpg"]	COMPLETED	2026-04-17 09:22:00+00
30	2026-04-04 11:04:52.477726+00	2026-04-06 13:28:44.633392+00	90.57	6	8	PM	Anouar achganiou\nAbdelmalik raif\nAbdlilah ait hamou\nWalid chaibiAnouar	Être attentif au vidage des poubelles.\nRespecter le FIFO dans le stock.\nVérifiez les DLC des produits dans le stock et dans la zone de confort. Veillez à utiliser en priorité les produits dont la date est la plus proche. Avant toute utilisation, assurez-vous de contrôler les DLC et d’utiliser les produits dans le bon ordre.	Barista ok \ngreeter ok	Besoin d’un seau d’eau, d’un manche à balai et d’un balai\nD'un tuyau d’arrosage.	\N	COMPLETED	2026-04-04 00:04:00+00
38	2026-04-07 14:23:13.28749+00	2026-04-08 13:20:05.034376+00	89.03	4	8	PM	ABDELMOUHAIMINE HARCHI\nWALID KHAIRI	Être attentif et très vigilant au niveau des dates d’expiration des produits.\nÊtre attentif au port du tablier et du badge nominatif.\nBesoin de carte sanitaire du sraff	Greeter ok \nBarista ok	Box pour conditionnement(Muffin,cookies,lemon cake, viennoiseries).	\N	COMPLETED	2026-04-03 16:22:00+00
28	2026-04-02 16:02:57.293799+00	2026-04-02 19:47:14.216668+00	94.97	9	8	AM	Amine essaaf\nHamza saber\nAyman elhilali\nFatima ezzabra\n	Besoin d'un Nettoyage fréquent de la terrasse.\n	Super gloo ok\nGreeter ok\nBarista ok	Besoin d'un \nBalai à serpillière\nD'une Serpillière\nDe torchon vessels  	\N	COMPLETED	2026-04-02 13:02:00+00
39	2026-04-08 13:20:40.229441+00	2026-04-08 14:11:26.342646+00	93.55	12	8	AM	Zined mohammedi\nHafssa Salki	Veuillez indiquer la date limite de consommation (DLC) sur tous les produits ouverts.	Greeter ok \nBarista ok	Reparation de l’afficheur du réfrigérateur .	["/static/uploads/3b019f29-c9f2-4597-acfe-f580ec05e1bc.jpg"]	COMPLETED	2026-04-04 09:00:00+00
41	2026-04-08 15:23:30.765916+00	2026-04-11 08:39:58.548857+00	89.31	1	8	AM	AYMANE EL HAJJAJI\nIKRAM ANTARI\nNIAMA BOUGHRARA  	autorisation du magasin et carte sanitaire  , doivent être disponible  sur place \netre attentif au vidage de poubelles\nfaire attention au dlc des produits ouvert\n\n	Greeter ok\nbarista  ok\n\n	timer brosse pour grille\ncouteau \nsandwishe\n porte labels\netagers pour les tasses\n	\N	COMPLETED	2026-04-07 00:30:00+00
42	2026-04-09 16:48:22.355178+00	2026-04-13 07:34:32.55073+00	92.45	3	8	AM	MOUHAMED NDIAYE\nFATIMA EZZAHRA EL KOUDRI\nANASS NADI	Etre attentif au vidage des poubelles .\nEntretenir les plantes.\n\n 	greeter ok\nBarista ok	Blender\nRéparer l’affichage  du congelateur \n\n	\N	COMPLETED	2026-04-07 13:00:00+00
45	2026-04-16 10:11:04.704015+00	2026-04-17 07:50:20.359043+00	92.45	13	8	AM	Gizlane Benlahlai  Greeter\nfattemezzahra   Barista\nChaabiya Berrak   cleaning\n	Réparer les ampoules.\nFaire attention au port du badge nominatif.\nÊtre attentif aux DLC des produits.	Gizlane Benlahlai  Greeter ok\nfattemezzahra   Barista ok	Ampoules	\N	COMPLETED	2026-04-16 05:10:00+00
27	2026-04-02 13:30:13.048806+00	2026-04-02 16:02:10.558817+00	91.82	10	8	AM	Youness ajmarik \nMarrakech boulikdame	R			\N	COMPLETED	2026-04-02 09:27:00+00
46	2026-04-17 10:41:41.836108+00	\N	0	1	4	AM					\N	IN_PROGRESS	2026-04-17 09:41:00+00
47	2026-04-17 10:42:16.317784+00	\N	0	1	4	AM					\N	IN_PROGRESS	2026-04-17 09:42:00+00
31	2026-04-06 13:28:58.233465+00	2026-04-07 10:31:16.344165+00	96.64	8	8	AM	Othmane sadik \nJardi oussma \nAyoub douki				\N	COMPLETED	2026-04-06 06:28:00+00
48	2026-04-17 10:48:10.438463+00	2026-04-17 11:29:07.539122+00	54.72	1	8	AM	Ayman rlhajjaj\nIkram antari\nKhalil samir				\N	IN_PROGRESS	2026-04-17 04:47:00+00
\.


--
-- Data for Name: coffees; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.coffees (id, name, location, active, ref) FROM stdin;
1	CARIBOU ANFA	Casablanca	t	CAF-04
3	CARIBOU BOURGOGNE 	Casablanca	t	CAF-05
2	CARIBOU CASA VOYAGEUR	Casablanca	t	CAF-06
8	CARIBOU CASA PORT	Casablanca	t	CAF-07
9	CARIBOU GHANDI	Casablanca	t	CAF-08
10	CARIBOU BACHKOU	Casablanca	t	CAF-09
11	CARIBOU 2 MARS 	Casablanca	t	CAF-10
12	CARIBOU BOUSKOURA 	Casablanca	t	CAF-11
13	CARIBOU DAR BOUAZZA 	Casablanca	t	CAF-12
14	CARIBOU GARE MARRAKECH 	Marrakech 	t	CAF-13
15	CARIBOU AL MAZAR	Marrakech 	t	CAF-14
4	CARIBOU RABAT AGDAL	Rabat	t	CAF-01
5	CARIBOU RIAD RABAT	Rabat	t	CAF-02
6	CARIBOU VILLA RABAT 	Rabat	t	CAF-03
\.


--
-- Data for Name: manager_coffees; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.manager_coffees (user_id, coffee_id) FROM stdin;
\.


--
-- Data for Name: user_rights; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_rights (id, user_id, coffees_read, coffees_create, coffees_update, coffees_delete, audits_read, audits_create, audits_update, audits_delete, users_read, users_create, users_update, users_delete, categories_read, categories_create, categories_update, categories_delete, questions_read, questions_create, questions_update, questions_delete) FROM stdin;
3	1	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
4	7	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
6	9	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
7	3	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
8	12	f	f	f	f	t	t	t	t	f	f	f	f	t	t	f	f	f	f	f	f
5	8	t	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
9	6	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f	f
1	4	f	f	f	f	t	t	f	f	f	f	f	f	f	f	f	f	f	f	f	f
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, full_name, is_active, role, coffee_id, receive_daily_report, receive_weekly_report, receive_monthly_report) FROM stdin;
1	admin@caribou.ma	$2b$12$VHN2R8B3/7/wkyiQ9UrSbeZYiSfEq9Ca3xC5qLBPl0xdaTsumHxjC	Admin	t	ADMIN	\N	f	f	f
8	Youssef.alaoui-soce@cariboucoffee.ma	$2b$12$lJh2gKYalGIQDJG28rtRKeA/J.HASH9ysRZeS/n5G6B/wZmQiPfJm	Youssef alaoui soce	t	AUDITOR	\N	f	f	f
6	zayd.baddouh@cariboucoffee.ma	$2b$12$jftAx29X.rJWDju.wE1UVesNMX44LVi.4wOsyo2hKJ5s/3Sp1cIiq	zayd baddouh	t	AUDITOR	\N	f	f	f
12	directeur@test.com	$2b$12$ie2MsjKNgxpCCjHS6jPzke9XxHoLmQEFcyNDCzELO8jdoDvdxsuCS	directeur test	t	BOSS	\N	f	f	f
7	Elbakhiche.mehdi@cariboucoffee.ma	$2b$12$afr0aUeP7LXuvhKAiDrYWefiEV2EQOmyXljGC0CIZpS2LJxFAdYFG	Elbakhiche mehdi	t	AUDITOR	\N	f	f	f
9	erroussafi.yassine@cariboucoffee.ma	$2b$12$WDErucQqbrqgV1qDlW9PIubdoQ7b9dhD2BYykn7g4uLk4m.rP6uO6	Yassine Erroussafi	t	ADMIN	\N	f	f	t
3	ilham.yardi@cariboucoffee.ma	$2b$12$Mk4iHrv7.kE216.9MuljJeFGwpYEWpTAG6HHqxbtPu3UKootfX52C	Ilham Yardi	t	AUDITOR	\N	f	f	t
4	saad.fahmi@cariboucoffee.ma	$2b$12$35xzSgaxa2SXmUXvigH7t.G9EQJynNnbCBmoLfT0wn67trPAAnApS	saad fahmi	t	BOSS	\N	f	f	f
11	test@cariboucoffee.ma	$2b$12$WgRGxr4sfbCN5C21eHSjeORrfxcneDBRNJWNu5fjA0HFwkqHtAXRa	test	t	AUDITOR	\N	f	f	f
\.


--
-- Name: audit_answers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_answers_id_seq', 144603, true);


--
-- Name: audit_categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_categories_id_seq', 11, true);


--
-- Name: audit_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_questions_id_seq', 78, true);


--
-- Name: audits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audits_id_seq', 50, true);


--
-- Name: coffees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.coffees_id_seq', 15, true);


--
-- Name: user_rights_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_rights_id_seq', 9, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 12, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_answers audit_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_answers
    ADD CONSTRAINT audit_answers_pkey PRIMARY KEY (id);


--
-- Name: audit_categories audit_categories_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_categories
    ADD CONSTRAINT audit_categories_name_key UNIQUE (name);


--
-- Name: audit_categories audit_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_categories
    ADD CONSTRAINT audit_categories_pkey PRIMARY KEY (id);


--
-- Name: audit_questions audit_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_questions
    ADD CONSTRAINT audit_questions_pkey PRIMARY KEY (id);


--
-- Name: audits audits_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audits
    ADD CONSTRAINT audits_pkey PRIMARY KEY (id);


--
-- Name: coffees coffees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coffees
    ADD CONSTRAINT coffees_pkey PRIMARY KEY (id);


--
-- Name: manager_coffees manager_coffees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manager_coffees
    ADD CONSTRAINT manager_coffees_pkey PRIMARY KEY (user_id, coffee_id);


--
-- Name: user_rights user_rights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_rights
    ADD CONSTRAINT user_rights_pkey PRIMARY KEY (id);


--
-- Name: user_rights user_rights_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_rights
    ADD CONSTRAINT user_rights_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_answers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_answers_id ON public.audit_answers USING btree (id);


--
-- Name: ix_audit_categories_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_categories_id ON public.audit_categories USING btree (id);


--
-- Name: ix_audit_questions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_questions_id ON public.audit_questions USING btree (id);


--
-- Name: ix_audits_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audits_id ON public.audits USING btree (id);


--
-- Name: ix_coffees_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_coffees_id ON public.coffees USING btree (id);


--
-- Name: ix_coffees_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_coffees_name ON public.coffees USING btree (name);


--
-- Name: ix_coffees_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_coffees_ref ON public.coffees USING btree (ref);


--
-- Name: ix_user_rights_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_user_rights_id ON public.user_rights USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: audit_answers audit_answers_audit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_answers
    ADD CONSTRAINT audit_answers_audit_id_fkey FOREIGN KEY (audit_id) REFERENCES public.audits(id);


--
-- Name: audit_answers audit_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_answers
    ADD CONSTRAINT audit_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.audit_questions(id);


--
-- Name: audit_questions audit_questions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_questions
    ADD CONSTRAINT audit_questions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.audit_categories(id);


--
-- Name: audits audits_auditor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audits
    ADD CONSTRAINT audits_auditor_id_fkey FOREIGN KEY (auditor_id) REFERENCES public.users(id);


--
-- Name: audits audits_coffee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audits
    ADD CONSTRAINT audits_coffee_id_fkey FOREIGN KEY (coffee_id) REFERENCES public.coffees(id);


--
-- Name: manager_coffees manager_coffees_coffee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manager_coffees
    ADD CONSTRAINT manager_coffees_coffee_id_fkey FOREIGN KEY (coffee_id) REFERENCES public.coffees(id);


--
-- Name: manager_coffees manager_coffees_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manager_coffees
    ADD CONSTRAINT manager_coffees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_rights user_rights_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_rights
    ADD CONSTRAINT user_rights_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_coffee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_coffee_id_fkey FOREIGN KEY (coffee_id) REFERENCES public.coffees(id);


--
-- PostgreSQL database dump complete
--

\unrestrict rAEjlS0x8O4RmHcgsDD6bF0x96u2cJzQB7olViwdAbX0aplpbvgOIGBJf0mEc58

