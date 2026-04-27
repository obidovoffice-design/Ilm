from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, Branch, Testimonial, Application, News, Slider, AboutContent, AboutFeature
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ilmplyus-secret-key-2025'

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    try:
        os.makedirs(instance_path)
    except Exception as e:
        print(f"Error creating instance directory: {e}")

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Absolute path is more reliable on Render
    db_path = os.path.join(instance_path, 'ilmplyus.db')
    db_url = f'sqlite:///{db_path}'
elif db_url.startswith('postgres://'):
    # Fix for newer SQLAlchemy versions
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ---------------------- AUTOMATIC DATABASE INITIALIZATION ----------------------
def seed_database():
    """Ma'lumotlar bazasini yaratish va admin qo'shish (Auto-seed)"""
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            email='admin@ilmplyus.uz',
            is_admin=True
        )
        db.session.add(admin)
        print("✅ Admin foydalanuvchi yaratildi: admin / admin123")

    if Course.query.count() == 0:
        courses = [
            Course(title='Ingliz tili',
                   description='Intensiv ingliz tili kurslari. Barcha darajalar: Beginner dan Advanced gacha. IELTS, CEFR tayyorgarlik.',
                   duration='3 oy', price="450 000 so'm/oy", icon='🇬🇧', category='til', level='Barcha darajalar', students_count=245),
            Course(title='Arab tili',
                   description="Arab tilini 0 dan boshlab o'rganing. Qur'on tilini tushunish imkoniyati.",
                   duration='4 oy', price="400 000 so'm/oy", icon='🇸🇦', category='til', level="Boshlang'ich", students_count=189),
            Course(title='Rus tili',
                   description="Ish va muloqot uchun rus tili. Grammatika va so'zlashuv amaliyoti.",
                   duration='3 oy', price="400 000 so'm/oy", icon='🇷🇺', category='til', level='Barcha darajalar', students_count=167),
            Course(title='Koreys tili',
                   description='Koreys tili va madaniyati. TOPIK imtihoniga tayyorgarlik.',
                   duration='4 oy', price="500 000 so'm/oy", icon='🇰🇷', category='til', level="Boshlang'ich", students_count=134),
            Course(title='Xitoy tili',
                   description='Xitoy tili iyerogliflari va talaffuzi. HSK 1-4 darajalariga tayyorgarlik.',
                   duration='5 oy', price="550 000 so'm/oy", icon='🇨🇳', category='til', level="Boshlang'ich", students_count=98),
            Course(title='Matematika',
                   description="Maktab o'quvchilari uchun matematika. DTM va imtihonlarga tayyorgarlik.",
                   duration='3 oy', price="350 000 so'm/oy", icon='🧮', category='fan', level='Barcha darajalar', students_count=156),
        ]
        db.session.add_all(courses)
        print("✅ Test kurslar qo'shildi")

    if Branch.query.count() == 0:
        branches = [
            Branch(name='Chilonzor filiali',
                   address='Chilonzor tumani, 9-kvartal, 12-uy (Chilonzor metrosi yonida)',
                   phone='+998 90 123 45 67', phone2='+998 71 234 56 78',
                   email='chilonzor@ilmplyus.uz', work_time='Dushanba-Shanba: 09:00 - 21:00',
                   work_time_saturday='09:00 - 18:00', latitude=41.2775, longitude=69.2146,
                   district='Chilonzor', features='Wi-Fi,Konditsioner,Kutubxona,Oshxona,Qulay parkovka', order=1, is_active=True),
            Branch(name='Yunusobod filiali',
                   address='Yunusobod tumani, 14-mavze, 5-uy (Minor masjidi yaqinida)',
                   phone='+998 90 765 43 21', phone2='+998 71 765 43 21',
                   email='yunusobod@ilmplyus.uz', work_time='Dushanba-Shanba: 09:00 - 21:00',
                   work_time_saturday='09:00 - 18:00', latitude=41.3689, longitude=69.2850,
                   district='Yunusobod', features='Wi-Fi,Konditsioner,Avtoturargoh,Monitorlar,Maxsus xona', order=2, is_active=True),
            Branch(name="Mirzo Ulug'bek filiali",
                   address="Mirzo Ulug'bek tumani, Buyuk Ipak Yoli, 45 (Markaz bozor yonida)",
                   phone='+998 90 987 65 43', phone2='+998 71 987 65 43',
                   email='mirzoulugbek@ilmplyus.uz', work_time='Dushanba-Shanba: 09:00 - 21:00',
                   work_time_saturday='09:00 - 17:00', latitude=41.3185, longitude=69.3219,
                   district="Mirzo Ulug'bek", features='Wi-Fi,Konditsioner,Kutubxona,Qulay parkovka', order=3, is_active=True),
        ]
        db.session.add_all(branches)
        print("✅ Test filiallar qo'shildi")

    db.session.commit()
    print("🎉 Database initialized and seeded!")

# Run initialization on startup
with app.app_context():
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---- Global context (barcha templateda ishlaydi) ----
@app.context_processor
def inject_globals():
    now = datetime.utcnow()
    new_applications_count = 0
    try:
        new_applications_count = Application.query.filter_by(status='new').count()
    except Exception:
        pass
    return dict(now=now, new_applications_count=new_applications_count)

# ---------------------- MA'LUMOTLAR BAZASINI YARATISH ----------------------
# ---------------------- CLI COMMANDS ----------------------
@app.cli.command("init-db")
def init_db_command():
    """Ma'lumotlar bazasini yaratish va admin qo'shish (Manual CLI)"""
    seed_database()
    print("✅ init-db command executed successfully.")

# ---------------------- ASOSIY SAHIFALAR ----------------------
@app.route('/')
def index():
    courses = []
    branches = []
    testimonials = []
    sliders = []
    about_content = None
    about_features = []

    try:
        courses = Course.query.filter_by(is_active=True).limit(6).all()
        branches = Branch.query.filter_by(is_active=True).order_by(Branch.order).all()
        testimonials = Testimonial.query.filter_by(is_active=True).all()
        sliders = Slider.query.filter_by(is_active=True).order_by(Slider.order).all()
        about_content = AboutContent.query.first()
        about_features = AboutFeature.query.filter_by(is_active=True).order_by(AboutFeature.order).all()
    except Exception as e:
        print(f"Xatolik: {e}")

    return render_template(
        'index.html',
        courses=courses,
        branches=branches,
        testimonials=testimonials,
        sliders=sliders,
        about=about_content,
        about_features=about_features
    )

@app.route('/courses')
def courses():
    try:
        category = request.args.get('category', 'all')
        if category and category != 'all':
            courses = Course.query.filter_by(is_active=True, category=category).all()
        else:
            courses = Course.query.filter_by(is_active=True).all()
        return render_template('courses.html', courses=courses, current_category=category)
    except Exception as e:
        print(f"Xatolik: {e}")
        return render_template('courses.html', courses=[], current_category='all')

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', course=course)

@app.route('/about')
def about():
    about_content = None
    about_features = []
    try:
        about_content = AboutContent.query.first()
        about_features = AboutFeature.query.filter_by(is_active=True).order_by(AboutFeature.order).all()
    except Exception as e:
        print(f"Xatolik: {e}")
    return render_template('about.html', about=about_content, about_features=about_features)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            application = Application(
                name=request.form.get('name'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                course_id=request.form.get('course_id') if request.form.get('course_id') else None,
                branch_id=request.form.get('branch_id') if request.form.get('branch_id') else None,
                message=request.form.get('message'),
                status='new'
            )
            db.session.add(application)
            db.session.commit()
            return jsonify({'success': True, 'message': "✅ Murojaatingiz qabul qilindi! Tez orada siz bilan bog'lanamiz."})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Xatolik yuz berdi: {str(e)}'})

    branches = Branch.query.filter_by(is_active=True).all()
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('contact.html', branches=branches, courses=courses)

@app.route('/news')
def news_list():
    try:
        page = request.args.get('page', 1, type=int)
        news = News.query.filter_by(is_active=True).order_by(News.created_at.desc()).paginate(page=page, per_page=9)
        return render_template('news.html', news=news.items, pagination=news)
    except Exception as e:
        print(f"Xatolik: {e}")
        return render_template('news.html', news=[], pagination=None)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    try:
        news = News.query.get_or_404(news_id)
        recent_news = News.query.filter_by(is_active=True).order_by(News.created_at.desc()).limit(6).all()
        return render_template('news_detail.html', news=news, recent_news=recent_news)
    except Exception:
        return redirect(url_for('news_list'))

@app.route('/api/branches')
def api_branches():
    branches = Branch.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': b.id, 'name': b.name, 'address': b.address, 'phone': b.phone,
        'phone2': b.phone2, 'email': b.email, 'work_time': b.work_time,
        'latitude': b.latitude, 'longitude': b.longitude, 'district': b.district,
        'features': b.features.split(',') if b.features else []
    } for b in branches])

# ---------------------- ADMIN PANEL ----------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login yoki parol xato!', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    courses_count = Course.query.count()
    branches_count = Branch.query.count()
    applications_count = Application.query.count()
    testimonials_count = Testimonial.query.count()
    recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           courses_count=courses_count,
                           branches_count=branches_count,
                           applications_count=applications_count,
                           testimonials_count=testimonials_count,
                           recent_applications=recent_applications)

# -------- KURSLAR --------
@app.route('/admin/courses')
@login_required
def admin_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/courses/add', methods=['GET', 'POST'])
@login_required
def admin_add_course():
    if request.method == 'POST':
        try:
            course = Course(
                title=request.form.get('title'),
                description=request.form.get('description'),
                duration=request.form.get('duration'),
                price=request.form.get('price'),
                icon=request.form.get('icon'),
                category=request.form.get('category'),
                level=request.form.get('level'),
                students_count=int(request.form.get('students_count', 0)),
                is_active='is_active' in request.form
            )
            db.session.add(course)
            db.session.commit()
            flash("✅ Kurs muvaffaqiyatli qo'shildi!", 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/add_course.html')

@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        try:
            course.title = request.form.get('title')
            course.description = request.form.get('description')
            course.duration = request.form.get('duration')
            course.price = request.form.get('price')
            course.icon = request.form.get('icon')
            course.category = request.form.get('category')
            course.level = request.form.get('level')
            course.students_count = int(request.form.get('students_count', 0))
            course.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Kurs muvaffaqiyatli yangilandi!', 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/courses/delete/<int:course_id>')
@login_required
def admin_delete_course(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        db.session.delete(course)
        db.session.commit()
        flash("✅ Kurs o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_courses'))

# -------- FILIALLAR --------
@app.route('/admin/branches')
@login_required
def admin_branches():
    branches = Branch.query.order_by(Branch.order).all()
    return render_template('admin/branches.html', branches=branches)

@app.route('/admin/branches/add', methods=['GET', 'POST'])
@login_required
def admin_add_branch():
    if request.method == 'POST':
        try:
            branch = Branch(
                name=request.form.get('name'),
                address=request.form.get('address'),
                phone=request.form.get('phone'),
                phone2=request.form.get('phone2'),
                email=request.form.get('email'),
                work_time=request.form.get('work_time'),
                work_time_saturday=request.form.get('work_time_saturday'),
                latitude=float(request.form.get('latitude', 41.3111)),
                longitude=float(request.form.get('longitude', 69.2797)),
                district=request.form.get('district'),
                features=','.join(request.form.getlist('features')) if request.form.getlist('features') else '',
                order=int(request.form.get('order', 0)),
                is_active='is_active' in request.form
            )
            db.session.add(branch)
            db.session.commit()
            flash("✅ Filial muvaffaqiyatli qo'shildi!", 'success')
            return redirect(url_for('admin_branches'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    districts = ['Chilonzor', 'Yunusobod', "Mirzo Ulug'bek", 'Yakkasaroy', 'Sergeli', 'Olmazor', 'Shayxontohur', 'Uchtepa']
    feature_options = ['Wi-Fi', 'Konditsioner', 'Kutubxona', 'Oshxona', 'Avtoturargoh', 'Monitor', 'Maxsus xona', 'Qulay parkovka']
    return render_template('admin/add_branch.html', districts=districts, features=feature_options)

@app.route('/admin/branches/edit/<int:branch_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    if request.method == 'POST':
        try:
            branch.name = request.form.get('name')
            branch.address = request.form.get('address')
            branch.phone = request.form.get('phone')
            branch.phone2 = request.form.get('phone2')
            branch.email = request.form.get('email')
            branch.work_time = request.form.get('work_time')
            branch.work_time_saturday = request.form.get('work_time_saturday')
            branch.latitude = float(request.form.get('latitude', branch.latitude))
            branch.longitude = float(request.form.get('longitude', branch.longitude))
            branch.district = request.form.get('district')
            branch.features = ','.join(request.form.getlist('features')) if request.form.getlist('features') else ''
            branch.order = int(request.form.get('order', branch.order))
            branch.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Filial muvaffaqiyatli yangilandi!', 'success')
            return redirect(url_for('admin_branches'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    districts = ['Chilonzor', 'Yunusobod', "Mirzo Ulug'bek", 'Yakkasaroy', 'Sergeli', 'Olmazor', 'Shayxontohur', 'Uchtepa']
    feature_options = ['Wi-Fi', 'Konditsioner', 'Kutubxona', 'Oshxona', 'Avtoturargoh', 'Monitor', 'Maxsus xona', 'Qulay parkovka']
    selected_features = branch.features.split(',') if branch.features else []
    return render_template('admin/edit_branch.html', branch=branch, districts=districts, features=feature_options, selected_features=selected_features)

@app.route('/admin/branches/delete/<int:branch_id>')
@login_required
def admin_delete_branch(branch_id):
    try:
        branch = Branch.query.get_or_404(branch_id)
        db.session.delete(branch)
        db.session.commit()
        flash("✅ Filial o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_branches'))

# -------- ARIZALAR --------
@app.route('/admin/applications')
@login_required
def admin_applications():
    status = request.args.get('status', 'all')
    from sqlalchemy.orm import joinedload
    q = Application.query.options(joinedload(Application.course), joinedload(Application.branch))
    if status and status != 'all':
        q = q.filter_by(status=status)
    applications = q.order_by(Application.created_at.desc()).all()
    return render_template('admin/applications.html', applications=applications, current_status=status)

@app.route('/admin/applications/<int:app_id>')
@login_required
def admin_view_application(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template('admin/view_application.html', app=application)

@app.route('/admin/applications/update/<int:app_id>', methods=['POST'])
@login_required
def admin_update_application(app_id):
    try:
        application = Application.query.get_or_404(app_id)
        application.status = request.form.get('status')
        db.session.commit()
        flash('✅ Ariza statusi yangilandi!', 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_applications'))

# -------- FIKRLAR --------
@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/testimonials/add', methods=['GET', 'POST'])
@login_required
def admin_add_testimonial():
    if request.method == 'POST':
        try:
            testimonial = Testimonial(
                name=request.form.get('name'),
                position=request.form.get('position'),
                text=request.form.get('text'),
                rating=int(request.form.get('rating', 5)),
                course_id=request.form.get('course_id') if request.form.get('course_id') else None,
                is_active='is_active' in request.form
            )
            db.session.add(testimonial)
            db.session.commit()
            flash("✅ Fikr muvaffaqiyatli qo'shildi!", 'success')
            return redirect(url_for('admin_testimonials'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('admin/add_testimonial.html', courses=courses)

@app.route('/admin/testimonials/edit/<int:testimonial_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    if request.method == 'POST':
        try:
            testimonial.name = request.form.get('name')
            testimonial.position = request.form.get('position')
            testimonial.text = request.form.get('text')
            testimonial.rating = int(request.form.get('rating', 5))
            testimonial.course_id = request.form.get('course_id') if request.form.get('course_id') else None
            testimonial.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Fikr muvaffaqiyatli yangilandi!', 'success')
            return redirect(url_for('admin_testimonials'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('admin/edit_testimonial.html', testimonial=testimonial, courses=courses)

@app.route('/admin/testimonials/delete/<int:testimonial_id>')
@login_required
def admin_delete_testimonial(testimonial_id):
    try:
        testimonial = Testimonial.query.get_or_404(testimonial_id)
        db.session.delete(testimonial)
        db.session.commit()
        flash("✅ Fikr o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_testimonials'))

# -------- YANGILIKLAR (Admin) --------
@app.route('/admin/news')
@login_required
def admin_news():
    news = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news.html', news=news)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    if request.method == 'POST':
        try:
            news = News(
                title=request.form.get('title'),
                content=request.form.get('content'),
                image_url=request.form.get('image_url'),
                is_active='is_active' in request.form
            )
            db.session.add(news)
            db.session.commit()
            flash("✅ Yangilik muvaffaqiyatli qo'shildi!", 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/add_news.html')

@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(news_id):
    news = News.query.get_or_404(news_id)
    if request.method == 'POST':
        try:
            news.title = request.form.get('title')
            news.content = request.form.get('content')
            news.image_url = request.form.get('image_url')
            news.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Yangilik yangilandi!', 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/edit_news.html', news=news)

@app.route('/admin/news/delete/<int:news_id>')
@login_required
def admin_delete_news(news_id):
    try:
        news = News.query.get_or_404(news_id)
        db.session.delete(news)
        db.session.commit()
        flash("✅ Yangilik o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_news'))

# -------- SLAYDERLAR (Admin) --------
@app.route('/admin/sliders')
@login_required
def admin_sliders():
    sliders = Slider.query.order_by(Slider.order).all()
    return render_template('admin/sliders.html', sliders=sliders)

@app.route('/admin/sliders/add', methods=['GET', 'POST'])
@login_required
def admin_add_slider():
    if request.method == 'POST':
        try:
            slider = Slider(
                title=request.form.get('title'),
                description=request.form.get('description'),
                image_url=request.form.get('image_url', 'img/slider1.png'),
                order=int(request.form.get('order', 0)),
                is_active='is_active' in request.form
            )
            db.session.add(slider)
            db.session.commit()
            flash("✅ Slayder qo'shildi!", 'success')
            return redirect(url_for('admin_sliders'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/add_slider.html')

@app.route('/admin/sliders/edit/<int:slider_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_slider(slider_id):
    slider = Slider.query.get_or_404(slider_id)
    if request.method == 'POST':
        try:
            slider.title = request.form.get('title')
            slider.description = request.form.get('description')
            slider.image_url = request.form.get('image_url')
            slider.order = int(request.form.get('order', slider.order))
            slider.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Slayder yangilandi!', 'success')
            return redirect(url_for('admin_sliders'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/edit_slider.html', slider=slider)

@app.route('/admin/sliders/delete/<int:slider_id>')
@login_required
def admin_delete_slider(slider_id):
    try:
        slider = Slider.query.get_or_404(slider_id)
        db.session.delete(slider)
        db.session.commit()
        flash("✅ Slayder o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_sliders'))

# -------- BIZ HAQIMIZDA (Admin) --------
@app.route('/admin/about-features')
@login_required
def admin_about_features():
    features = AboutFeature.query.order_by(AboutFeature.order).all()
    about = AboutContent.query.first()
    return render_template('admin/about_features.html', features=features, about=about)

@app.route('/admin/about/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_about():
    about = AboutContent.query.first()
    if request.method == 'POST':
        try:
            if about:
                about.title = request.form.get('title')
                about.description_1 = request.form.get('description_1')
                about.description_2 = request.form.get('description_2')
                about.description_3 = request.form.get('description_3')
                about.experience_years = int(request.form.get('experience_years', 14))
                about.image_url = request.form.get('image_url')
            else:
                about = AboutContent(
                    title=request.form.get('title'),
                    description_1=request.form.get('description_1'),
                    description_2=request.form.get('description_2'),
                    description_3=request.form.get('description_3'),
                    experience_years=int(request.form.get('experience_years', 14)),
                    image_url=request.form.get('image_url')
                )
                db.session.add(about)
            db.session.commit()
            flash('✅ Ma\'lumotlar yangilandi!', 'success')
            return redirect(url_for('admin_about_features'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/edit_about.html', about=about)

@app.route('/admin/about-features/add', methods=['GET', 'POST'])
@login_required
def admin_add_about_feature():
    if request.method == 'POST':
        try:
            feature = AboutFeature(
                title=request.form.get('title'),
                description=request.form.get('description'),
                icon=request.form.get('icon', 'fas fa-check-circle'),
                order=int(request.form.get('order', 0)),
                is_active='is_active' in request.form
            )
            db.session.add(feature)
            db.session.commit()
            flash("✅ Xususiyat qo'shildi!", 'success')
            return redirect(url_for('admin_about_features'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/add_about_feature.html')

@app.route('/admin/about-features/edit/<int:feature_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_about_feature(feature_id):
    feature = AboutFeature.query.get_or_404(feature_id)
    if request.method == 'POST':
        try:
            feature.title = request.form.get('title')
            feature.description = request.form.get('description')
            feature.icon = request.form.get('icon')
            feature.order = int(request.form.get('order', feature.order))
            feature.is_active = 'is_active' in request.form
            db.session.commit()
            flash('✅ Xususiyat yangilandi!', 'success')
            return redirect(url_for('admin_about_features'))
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
    return render_template('admin/edit_about_feature.html', feature=feature)

@app.route('/admin/about-features/delete/<int:feature_id>')
@login_required
def admin_delete_about_feature(feature_id):
    try:
        feature = AboutFeature.query.get_or_404(feature_id)
        db.session.delete(feature)
        db.session.commit()
        flash("✅ Xususiyat o'chirildi!", 'success')
    except Exception as e:
        flash(f'❌ Xatolik: {str(e)}', 'danger')
    return redirect(url_for('admin_about_features'))

# -------- PROFIL --------
@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            new_password = request.form.get('new_password')
            
            user = User.query.get(current_user.id)
            user.username = username
            user.email = email
            
            if new_password:
                user.password = generate_password_hash(new_password)
            
            db.session.commit()
            flash('✅ Profil muvaffaqiyatli yangilandi!', 'success')
        except Exception as e:
            flash(f'❌ Xatolik: {str(e)}', 'danger')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin/profile.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
