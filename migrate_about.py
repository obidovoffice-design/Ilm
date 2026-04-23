from app import app
from models import db, AboutContent, AboutFeature
import os

def migrate():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Seed AboutContent if empty
        if AboutContent.query.count() == 0:
            about = AboutContent(
                title="Biz haqimizda",
                description_1="\"ILM PLYUS O‘QUV\" nodavlat ta'lim muassasasi - o‘quv markazi, barcha xorijiy tillarni o‘rgatish bo‘yicha xizmat ko‘rsatadi. O‘quv markazi 2010-yilda tashkil etilgan.",
                description_2="Biz faoliyatimizni O‘zbekiston qonunchiligi asosida yuritamiz va sizga eng yaxshi ta'limni taqdim etamiz.",
                description_3="\"ILM PLYUS O‘QUV\" NTM o‘z faoliyatini O‘zbekiston Respublikasi qonunchiligiga binoan to‘g‘ridan-to‘g‘ri muassasada ishlab chiqilgan me'yoriy hujjatlar asosida qurilgan.",
                experience_years=14,
                image_url="https://images.unsplash.com/photo-1577896851231-70ef18881754?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
            )
            db.session.add(about)
            print("AboutContent seeded.")
        
        # Seed AboutFeature if empty
        if AboutFeature.query.count() == 0:
            features = [
                AboutFeature(title="Tajribali o'qituvchilar", description="14 yillik ta'lim sohasidagi tajriba va minglab muvaffaqiyatli bitiruvchilar", icon="fas fa-check-circle", order=1),
                AboutFeature(title="Zamonaviy o'quv xonalari", description="Kommunikativ metodika, interaktiv darslar va zamonaviy o'quv materiallari", icon="fas fa-check-circle", order=2),
                AboutFeature(title="Moslashuvchan jadval", description="Shaharning turli hududlarida joylashgan 6 ta filial, sizga yaqin manzilda", icon="fas fa-check-circle", order=3),
                AboutFeature(title="Sertifikat berish", description="Kurs yakunida davlat namunasidagi sertifikat va bitiruvchilar bilan ishlash", icon="fas fa-check-circle", order=4)
            ]
            db.session.add_all(features)
            print("AboutFeatures seeded.")
        
        db.session.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
