"""Add patient_id and file_type to uploaded_files and photo_medical_record_association table

Revision ID: 001
Revises: 
Create Date: 2025-08-21 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to uploaded_files table
    op.add_column('uploaded_files', sa.Column('file_type', sa.String(length=50), nullable=True))
    op.add_column('uploaded_files', sa.Column('patient_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint for patient_id
    op.create_foreign_key(
        'fk_uploaded_files_patient_id',
        'uploaded_files', 'users',
        ['patient_id'], ['id']
    )
    
    # Create photo_medical_record_association table
    op.create_table(
        'photo_medical_record_association',
        sa.Column('photo_id', sa.Integer(), nullable=False),
        sa.Column('medical_record_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['uploaded_files.id']),
        sa.ForeignKeyConstraint(['medical_record_id'], ['medical_records.id']),
        sa.PrimaryKeyConstraint('photo_id', 'medical_record_id')
    )
    
    # Update existing data: set file_type based on mime_type and patient_id = user_id for existing records
    connection = op.get_bind()
    
    # Set file_type for existing files
    connection.execute(
        sa.text("""
        UPDATE uploaded_files 
        SET file_type = CASE 
            WHEN mime_type LIKE 'image/%' THEN 'photo'
            ELSE 'medical_record'
        END
        WHERE file_type IS NULL
        """)
    )
    
    # Set patient_id = user_id for existing files (assuming uploader is the patient initially)
    connection.execute(
        sa.text("""
        UPDATE uploaded_files 
        SET patient_id = user_id 
        WHERE patient_id IS NULL
        """)
    )
    
    # Make columns non-nullable after updating data
    op.alter_column('uploaded_files', 'file_type', nullable=False)
    op.alter_column('uploaded_files', 'patient_id', nullable=False)

def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_uploaded_files_patient_id', 'uploaded_files', type_='foreignkey')
    
    # Drop photo_medical_record_association table
    op.drop_table('photo_medical_record_association')
    
    # Remove columns
    op.drop_column('uploaded_files', 'patient_id')
    op.drop_column('uploaded_files', 'file_type')
