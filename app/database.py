#C:\Users\Sujal\Downloads\Project Management Assistant Functional Features Overview\app\database.py

# ============================================================
# IMPORTS: Bringing in tools we need
# ============================================================

# Typing tools - help Python understand what data types we're working with
from typing import List, Optional, TypeVar, Type
# List = for lists of items [item1, item2, item3]
# Optional = for values that might be None (empty)
# TypeVar = creates a flexible type variable
# Type = represents a class type

# ObjectId - MongoDB's unique ID system (like a barcode for each document)
from bson import ObjectId

# Motor - async MongoDB driver (lets us talk to database without freezing the app)
from motor.motor_asyncio import AsyncIOMotorDatabase

# Pydantic - validates and structures our data (like a smart form)
from pydantic import BaseModel

# ============================================================
# TYPE VARIABLE: Create a flexible placeholder for any model
# ============================================================

# ModelType can be Member, Project, Task, or any Pydantic model
# Like a variable that can hold different types of forms
ModelType = TypeVar('ModelType', bound=BaseModel)

# ============================================================
# DATABASE CLASS: Universal toolbox for database operations
# ============================================================

class Database:
    """
    A class to handle all database operations for a specific collection.
    Uses the motor async client.
    
    Think of this as a universal remote control that works with 
    any MongoDB collection (members, projects, tasks, etc.)
    """
    
    # ========================================================
    # CONSTRUCTOR: Setup the database handler
    # ========================================================
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, model: Type[ModelType]):
        """
        Initialize the Database handler.
        
        Parameters:
        - db: The MongoDB database connection (like your WiFi connection)
        - collection_name: Name of collection to work with (like "members", "tasks")
        - model: The Pydantic model to use (like Member, Task classes)
        
        Example:
        member_db = Database(db, "members", Member)
        """
        # Store the specific collection we're working with
        # Like bookmarking the exact folder in a filing cabinet
        self.collection = db[collection_name]
        
        # Store the model we'll use to validate data
        # Like keeping a copy of the form template
        self.model = model

    # ========================================================
    # CREATE: Insert a new document into the database
    # ========================================================
    
    async def create(self, data: BaseModel) -> ModelType:
        """
        Inserts a new document into the collection.
        
        Parameter:
        - data: The Pydantic model with data to insert
        
        Returns:
        - The newly created document as a Pydantic model
        
        Example:
        new_member = await db.create(Member(name="John", email="john@email.com"))
        """
        
        # STEP 1: Convert Pydantic model to dictionary
        # Like converting a filled form into a simple key-value list
        document = data.model_dump(
            by_alias=True,        # Use alias names (_id instead of id)
            exclude_none=True,    # Don't include empty fields
            exclude={'id'}        # Don't include id (MongoDB creates _id automatically)
        )
        # Example result: {"name": "John", "email": "john@email.com", "role": "Developer"}
        
        # STEP 2: Convert string IDs to MongoDB ObjectId format
        # Loop through each field in the document
        for key, value in document.items():
            
            # If the value is a list (like assigned_to: ["id1", "id2"])
            if isinstance(value, list):
                # Convert each valid string ID in the list to ObjectId
                # Like converting multiple ticket numbers to barcode format
                document[key] = [
                    ObjectId(v) if ObjectId.is_valid(v) else v 
                    for v in value
                ]
                # Example: ["507f1f77bcf86cd799439011"] → [ObjectId("507f1f77bcf86cd799439011")]
            
            # If the value is a single string that looks like an ObjectId
            elif ObjectId.is_valid(value):
                # Convert the string to ObjectId
                # Like converting a single ticket number to barcode
                document[key] = ObjectId(value)
                # Example: "507f1f77bcf86cd799439011" → ObjectId("507f1f77bcf86cd799439011")

        # STEP 3: Insert the document into MongoDB
        # Like submitting the form to the database
        result = await self.collection.insert_one(document)
        
        # STEP 4: Fetch the newly created document from database
        # Why? Because MongoDB adds _id and other fields, we want the complete document
        # Like getting your receipt after making a purchase
        new_document = await self.collection.find_one({"_id": result.inserted_id})
        
        # STEP 5: Convert the MongoDB document back to Pydantic model
        # Like converting the receipt into a structured format
        # This validates the data and gives us type hints
        return self.model.model_validate(new_document)

    # ========================================================
    # READ BY ID: Get a single document by its ID
    # ========================================================
    
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        Retrieves a single document by its ObjectId string.
        
        Parameter:
        - id: The document ID as a string (like "507f1f77bcf86cd799439011")
        
        Returns:
        - The document as a Pydantic model, or None if not found
        
        Example:
        member = await db.get_by_id("507f1f77bcf86cd799439011")
        """
        
        # STEP 1: Check if the ID format is valid
        # MongoDB ObjectIds are 24 character hex strings
        # Like checking if a barcode is the right format
        if not ObjectId.is_valid(id):
            return None  # Invalid ID, return nothing
        
        # STEP 2: Search for the document in MongoDB
        # Like looking up a person by their ID card number
        document = await self.collection.find_one({"_id": ObjectId(id)})
        
        # STEP 3: If found, convert to Pydantic model and return
        if document:
            # Convert MongoDB document to our model format
            return self.model.model_validate(document)
        
        # STEP 4: If not found, return None
        return None

    # ========================================================
    # READ ALL: Get all documents with pagination
    # ========================================================
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Retrieves all documents in the collection with pagination.
        
        Parameters:
        - skip: Number of documents to skip (default: 0, start from beginning)
        - limit: Maximum number of documents to return (default: 100)
        
        Returns:
        - List of documents as Pydantic models
        
        Example:
        # Get first 10 members
        members = await db.get_all(skip=0, limit=10)
        
        # Get next 10 members (like page 2)
        members = await db.get_all(skip=10, limit=10)
        """
        
        # STEP 1: Create a query cursor
        # .find() = get all documents
        # .skip(skip) = skip the first N documents (for pagination)
        # .limit(limit) = only return maximum N documents
        # Like saying "show me page 2, with 10 items per page"
        cursor = self.collection.find().skip(skip).limit(limit)
        
        # STEP 2: Execute the query and convert to list
        # Like actually fetching the results from the database
        documents = await cursor.to_list(length=limit)
        
        # STEP 3: Convert each MongoDB document to Pydantic model
        # List comprehension loops through each document and converts it
        # Like converting multiple receipts into structured records
        return [self.model.model_validate(doc) for doc in documents]

    # ========================================================
    # UPDATE: Modify an existing document
    # ========================================================
    
    async def update(self, id: str, data: BaseModel) -> Optional[ModelType]:
        """
        Updates an existing document by its ObjectId string.
        
        Parameters:
        - id: The document ID to update
        - data: Pydantic model with fields to update (only include changed fields)
        
        Returns:
        - The updated document as a Pydantic model, or None if not found
        
        Example:
        updated_member = await db.update(
            "507f1f77bcf86cd799439011",
            MemberUpdate(role="Senior Developer")
        )
        """
        
        # STEP 1: Validate the ID format
        # Like checking if the barcode is readable
        if not ObjectId.is_valid(id):
            return None  # Invalid ID, can't update
        
        # STEP 2: Convert update data to dictionary
        # Only include fields that are set (not None)
        # Like listing only the fields you want to change on a form
        update_data = data.model_dump(
            by_alias=True,        # Use alias names
            exclude_none=True,    # Only include fields with values
            exclude={'id'}        # Don't try to update the ID field
        )
        
        # STEP 3: Convert string IDs to ObjectId format
        # Same process as in create() method
        for key, value in update_data.items():
            # Handle lists of IDs
            if isinstance(value, list):
                update_data[key] = [
                    ObjectId(v) if ObjectId.is_valid(v) else v 
                    for v in value
                ]
            # Handle single IDs
            elif ObjectId.is_valid(value):
                update_data[key] = ObjectId(value)

        # STEP 4: Perform the update in MongoDB
        # update_one() updates a single document
        # {"_id": ObjectId(id)} = find document with this ID
        # {"$set": update_data} = set these fields to new values
        # Like finding a file and updating specific lines
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},      # Which document to update (filter)
            {"$set": update_data}        # What to update (new values)
        )
        
        # STEP 5: Check if update was successful
        
        # Case 1: Something was actually modified
        if result.modified_count == 1:
            # Fetch and return the updated document
            return await self.get_by_id(id)
        
        # Case 2: Document was found but no changes made
        # (This happens when update data is same as existing data)
        if result.matched_count == 1 and result.modified_count == 0:
            # Still return the document (even though nothing changed)
            return await self.get_by_id(id)

        # Case 3: Document not found at all
        return None

    # ========================================================
    # DELETE: Remove a document from the database
    # ========================================================
    
    async def delete(self, id: str) -> bool:
        """
        Deletes a document by its ObjectId string.
        
        Parameter:
        - id: The document ID to delete
        
        Returns:
        - True if deleted successfully, False otherwise
        
        Example:
        was_deleted = await db.delete("507f1f77bcf86cd799439011")
        if was_deleted:
            print("Member deleted!")
        """
        
        # STEP 1: Validate the ID format
        if not ObjectId.is_valid(id):
            return False  # Invalid ID, can't delete
        
        # STEP 2: Delete the document from MongoDB
        # delete_one() removes a single document
        # Like shredding a specific file from a filing cabinet
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        
        # STEP 3: Return True if exactly 1 document was deleted
        # deleted_count is 1 if successful, 0 if document wasn't found
        return result.deleted_count == 1


# ============================================================
# USAGE EXAMPLES
# ============================================================

"""
# Example 1: Working with Members
member_db = Database(mongodb, "members", Member)

# Create a new member
new_member = await member_db.create(
    Member(name="Alice", email="alice@email.com", role="Developer")
)
# Result: Alice added with ID "507f1f77bcf86cd799439011"

# Get member by ID
alice = await member_db.get_by_id("507f1f77bcf86cd799439011")
# Result: Member(name="Alice", email="alice@email.com", ...)

# Get all members (first 10)
all_members = await member_db.get_all(skip=0, limit=10)
# Result: [Member(...), Member(...), ...]

# Update member
updated = await member_db.update(
    "507f1f77bcf86cd799439011",
    MemberUpdate(role="Senior Developer")
)
# Result: Alice's role is now "Senior Developer"

# Delete member
deleted = await member_db.delete("507f1f77bcf86cd799439011")
# Result: True (Alice removed from database)
"""