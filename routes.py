from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, GrinderSettings, Shot, Coffee
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI, GRINDER_SETTINGS, COFFEE_SETTINGS
from sqlalchemy import func

def is_valid_step(value, min_value, step_size):
    """Check if the value follows the step size pattern from the minimum."""
    steps = (value - min_value) / step_size
    return abs(steps - round(steps)) < 0.0001

def get_last_shot(user_id, coffee_id=None):
    """Get the most recent shot for the user, optionally filtered by coffee."""
    query = Shot.query.filter_by(user_id=user_id)
    if coffee_id:
        query = query.filter_by(coffee_id=coffee_id)
    
    shot = query.order_by(Shot.date.desc()).first()
    if shot:
        return {
            'coffee_id': shot.coffee_id,
            'grind_size': shot.grind_size,
            'coffee_weight': shot.coffee_weight,
            'shot_yield': shot.shot_yield,
            'shot_time': shot.shot_time,
            'taste': shot.taste,
            'body': shot.body
        }
    return None

def init_routes(app, limiter):
    @app.route('/')
    @login_required
    def index():
        settings = GrinderSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = GrinderSettings(current_user.id)
            db.session.add(settings)
            db.session.commit()

        # Get all active coffees (those with grams > 0)
        coffees = Coffee.query.filter_by(user_id=current_user.id)\
                             .filter(Coffee.grams > 0)\
                             .order_by(Coffee.created_at.desc())\
                             .all()
        
        # Get the last shot and its coffee_id
        last_shot = get_last_shot(current_user.id)
        default_coffee_id = last_shot['coffee_id'] if last_shot else None

        # Get user statistics
        stats = Shot.get_user_stats(current_user.id)
        
        # Update context with all required data
        context = {
            'coffees': coffees,
            'default_coffee_id': default_coffee_id,
            'grinder_settings': settings,
            'last_shot': last_shot,
            'config': app.config,
            'grind_size_error': request.args.get('grind_size_error'),
            'today_shots_count': stats['today_shots_count'],
            'total_shots_count': stats['total_shots_count'],
            'avg_rating': stats['avg_rating'],
            'active_coffees_count': Coffee.query.filter(
                Coffee.user_id == current_user.id,
                Coffee.grams > 0
            ).count()
        }
        
        return render_template('index.html', **context)

    @app.route('/submit_shot', methods=['POST'])
    @login_required
    def submit_shot():
        try:
            coffee = Coffee.query.get(request.form['coffee_id'])
            if not coffee or coffee.user_id != current_user.id:
                raise ValueError("Invalid coffee selection")
            
            # Update remaining coffee amount
            coffee.grams -= float(request.form['coffee_weight'])
            if coffee.grams < 0:
                raise ValueError("Not enough coffee remaining")
            
            new_shot = Shot(
                user_id=current_user.id,
                coffee_id=coffee.id,
                grind_size=float(request.form['grind_size']),
                coffee_weight=float(request.form['coffee_weight']),
                shot_time=float(request.form['shot_time']),
                shot_yield=float(request.form['shot_yield']),
                taste=int(request.form['taste']),
                body=int(request.form['body']),
                notes=request.form.get('notes', '')
            )
            
            settings = GrinderSettings.query.filter_by(user_id=current_user.id).first()
            if settings:
                settings.last_used_size = new_shot.grind_size
            
            db.session.add(new_shot)
            db.session.commit()
            flash('Shot recorded successfully!', 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f'Error recording shot: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error recording shot: {str(e)}', 'error')
        
        return redirect(url_for('index'))

    @app.route('/history')
    @login_required
    def history():
        shots = Shot.query.filter_by(user_id=current_user.id)\
                         .order_by(Shot.date.desc())\
                         .all()
        
        grouped_shots = {}
        for shot in shots:
            month_year = shot.date.strftime('%B %Y')
            if month_year not in grouped_shots:
                grouped_shots[month_year] = []
            
            grouped_shots[month_year].append({
                'id': shot.id,
                'formatted_date': shot.date.strftime('%Y-%m-%d %H:%M'),
                'grind_size': shot.grind_size,
                'coffee_weight': shot.coffee_weight,
                'shot_yield': shot.shot_yield,
                'shot_time': shot.shot_time,
                'taste': shot.taste,
                'body': shot.body
            })
        
        return render_template('history.html', grouped_shots=grouped_shots, GRINDER_SETTINGS=GRINDER_SETTINGS)

    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html', GRINDER_SETTINGS=GRINDER_SETTINGS)

    @app.route('/grinder_settings', methods=['GET', 'POST'])
    @login_required
    def grinder_settings():
        settings = GrinderSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = GrinderSettings(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()

        if request.method == 'POST':
            try:
                grinder_type = request.form['grinder_type']
                # Validate grinder type
                if grinder_type not in GRINDER_SETTINGS['GRINDER_TYPE']['options']:
                    raise ValueError("Invalid grinder type")
                    
                min_size = float(request.form['min_size'])
                max_size = float(request.form['max_size'])
                
                # Set step size based on grinder type
                if grinder_type == 'stepped':
                    if 'step_size' not in request.form:
                        raise ValueError("Step size is required for stepped grinders")
                    step_size = float(request.form['step_size'])
                    if step_size <= 0:
                        raise ValueError("Step size must be greater than 0")
                else:
                    step_size = 0.01  # Default small step for stepless grinders
                
                if min_size >= max_size:
                    raise ValueError("Minimum size must be less than maximum size")
                
                settings.grinder_type = grinder_type
                settings.min_size = min_size
                settings.max_size = max_size
                settings.step_size = step_size
                settings.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash('Grinder settings updated successfully!', 'success')
                return redirect(url_for('index'))
                
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('grinder_settings'))
        
        return render_template('grinder_settings.html', settings=settings, GRINDER_SETTINGS=GRINDER_SETTINGS)

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("500 per minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                username = request.form['username']
                password = request.form['password']
                
                user = User.query.filter_by(username=username).first()
                if user and check_password_hash(user.password, password):
                    login_user(user, remember=False)  # Disable remember me for security
                    return redirect(url_for('index'))
                
                flash('Invalid username or password', 'error')
            except Exception as e:
                flash(f'Login failed: {str(e)}', 'error')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("500 per minute")
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            try:
                username = request.form['username']
                password = request.form['password']
                
                # Validate username
                if not username or len(username) < 3:
                    flash('Username must be at least 3 characters long', 'error')
                    return redirect(url_for('register'))
                
                if User.query.filter_by(username=username).first():
                    flash('Username already exists', 'error')
                    return redirect(url_for('register'))
                
                # Create new user with password validation
                new_user = User(username=username)
                try:
                    new_user.set_password(password)
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('register'))
                
                db.session.add(new_user)
                db.session.commit()
                
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                flash(f'Registration failed: {str(e)}', 'error')
        
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login')) 

    @app.route('/coffee', methods=['GET'])
    @login_required
    def coffee_list():
        coffees = Coffee.query.filter_by(user_id=current_user.id).order_by(Coffee.created_at.desc()).all()
        return render_template('coffee.html', 
                             coffees=coffees,
                             COFFEE_SETTINGS=COFFEE_SETTINGS)

    @app.route('/add_coffee', methods=['GET', 'POST'])
    @login_required
    def add_coffee():
        if request.method == 'POST':
            try:
                new_coffee = Coffee(
                    user_id=current_user.id,
                    name=request.form['name'],
                    roaster=request.form['roaster'],
                    roast_date=datetime.strptime(request.form['roast_date'], '%Y-%m-%d').date(),
                    tasting_notes=request.form.get('tasting_notes', ''),
                    grams=float(request.form['grams'])
                )
                db.session.add(new_coffee)
                db.session.commit()
                flash('Coffee added successfully!', 'success')
                return redirect(url_for('coffee_list'))
            except Exception as e:
                flash(f'Error adding coffee: {str(e)}', 'error')
        
        return render_template('coffee.html', 
                             coffees=Coffee.query.filter_by(user_id=current_user.id).all(),
                             COFFEE_SETTINGS=COFFEE_SETTINGS)

    @app.route('/edit_coffee/<int:coffee_id>', methods=['GET', 'POST'])
    @login_required
    def edit_coffee(coffee_id):
        coffee = Coffee.query.get_or_404(coffee_id)
        
        # Ensure user owns this coffee
        if coffee.user_id != current_user.id:
            flash('Access denied', 'error')
            return redirect(url_for('coffee_list'))
        
        if request.method == 'POST':
            try:
                coffee.name = request.form['name']
                coffee.roaster = request.form['roaster']
                coffee.roast_date = datetime.strptime(request.form['roast_date'], '%Y-%m-%d').date()
                coffee.tasting_notes = request.form.get('tasting_notes', '')
                coffee.grams = float(request.form['grams'])
                
                db.session.commit()
                flash('Coffee updated successfully!', 'success')
                return redirect(url_for('coffee_list'))
            except Exception as e:
                flash(f'Error updating coffee: {str(e)}', 'error')
        
        return render_template('edit_coffee.html', 
                             coffee=coffee,
                             COFFEE_SETTINGS=COFFEE_SETTINGS)

    @app.route('/delete_coffee/<int:coffee_id>', methods=['POST'])
    @login_required
    def delete_coffee(coffee_id):
        coffee = Coffee.query.get_or_404(coffee_id)
        
        # Ensure user owns this coffee
        if coffee.user_id != current_user.id:
            flash('Access denied', 'error')
            return redirect(url_for('coffee_list'))
        
        try:
            db.session.delete(coffee)
            db.session.commit()
            flash('Coffee deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting coffee: {str(e)}', 'error')
        
        return redirect(url_for('coffee_list'))

    @app.route('/get_last_shot/<int:coffee_id>')
    @login_required
    def get_last_coffee_shot(coffee_id):
        coffee = Coffee.query.get_or_404(coffee_id)
        if coffee.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        last_shot = get_last_shot(current_user.id, coffee_id)
        return jsonify(last_shot if last_shot else {})
 